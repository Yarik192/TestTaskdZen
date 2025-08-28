import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from posts.models import Post
from django.db.models import Q
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied
from .jwt_utils import create_jwt_token, get_user_from_context, require_auth


class UserType(DjangoObjectType):
    first_name = graphene.String(source="first_name")
    last_name = graphene.String(source="last_name")
    date_joined = graphene.DateTime(source="date_joined")
    
    class Meta:
        model = User
        fields = ("id", "username", "email")


class AuthenticatedUserType(DjangoObjectType):
    first_name = graphene.String(source="first_name")
    last_name = graphene.String(source="last_name")
    date_joined = graphene.DateTime(source="date_joined")
    is_staff = graphene.Boolean(source="is_staff")
    
    class Meta:
        model = User
        fields = ("id", "username", "email")


class PostType(DjangoObjectType):
    timestamp = graphene.DateTime(source="timestamp")
    parent_post = graphene.Field("graphql_app.schema.PostType", source="parent_post")
    
    class Meta:
        model = Post
        fields = ("id", "text", "username", "email", "image", "text_file")

    def resolve_parent_post(self, info):
        return self.parent_post

    def resolve_replies(self, info):
        return Post.objects.filter(parent_post=self)


class CommentType(DjangoObjectType):
    timestamp = graphene.DateTime(source="timestamp")
    parent_post = graphene.Field("graphql_app.schema.PostType", source="parent_post")
    
    class Meta:
        model = Post
        fields = ("id", "text", "username")


class PostConnection(graphene.relay.Connection):
    class Meta:
        node = PostType


class PostNode(DjangoObjectType):
    timestamp = graphene.DateTime(source="timestamp")
    parent_post = graphene.Field("graphql_app.schema.PostType", source="parent_post")
    
    class Meta:
        model = Post
        interfaces = (graphene.relay.Node,)
        fields = ("id", "text", "username")



class ElasticsearchHitType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    text = graphene.String()
    timestamp = graphene.DateTime()
    parent_post_id = graphene.Int()
    score = graphene.Float()


class ElasticsearchAggregationType(graphene.ObjectType):
    usernames = graphene.JSONString()
    dates = graphene.JSONString()


class ElasticsearchSearchResult(graphene.ObjectType):
    hits = graphene.List(ElasticsearchHitType)
    total = graphene.Int()
    aggregations = graphene.Field(ElasticsearchAggregationType)
    query = graphene.String()
    filters = graphene.JSONString()


class SearchStatistics(graphene.ObjectType):
    total_posts = graphene.Int()
    unique_users = graphene.Int()
    posts_by_date = graphene.JSONString()


class Query(graphene.ObjectType):
    all_users = graphene.List(UserType, 
                            search=graphene.String(),
                            first=graphene.Int(),
                            skip=graphene.Int())
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    user_by_username = graphene.Field(UserType, username=graphene.String(required=True))
    
    all_posts = graphene.List(PostType, 
                             search=graphene.String(),
                             author_id=graphene.ID(),
                             parent_post_id=graphene.ID())
    post = graphene.Field(PostType, id=graphene.ID(required=True))
    user_posts = graphene.List(PostType, user_id=graphene.ID(required=True))
    
    posts_connection = graphene.relay.ConnectionField(PostConnection)
    
    post_comments = graphene.List(CommentType, post_id=graphene.ID(required=True))
    
    search_posts = graphene.List(PostType, query=graphene.String(required=True))
    
    elasticsearch_search = graphene.Field("graphql_app.schema.ElasticsearchSearchResult", 
                                        query=graphene.String(),
                                        size=graphene.Int(),
                                        from_=graphene.Int(),
                                        filters=graphene.JSONString())
    
    search_suggestions = graphene.List(graphene.String, query=graphene.String(required=True))
    
    search_statistics = graphene.Field("graphql_app.schema.SearchStatistics")
    search_users = graphene.List(UserType, query=graphene.String(required=True))
    
    me = graphene.Field(AuthenticatedUserType)

    def resolve_all_users(self, info, search=None, first=None, skip=None):
        users = User.objects.all()
        if search:
            users = users.filter(
                Q(username__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search)
            )
        
        if skip:
            users = users[skip:]
        if first:
            users = users[:first]
            
        return users

    def resolve_user(self, info, id):
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            raise GraphQLError(f"Пользователь с ID {id} не найден")

    def resolve_user_by_username(self, info, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise GraphQLError(f"Пользователь с именем \"{username}\" не найден")

    def resolve_all_posts(self, info, search=None, author_id=None, parent_post_id=None):
        posts = Post.objects.all().order_by("-timestamp")
        
        if search:
            posts = posts.filter(text__icontains=search)
        if author_id:
            posts = posts.filter(username__icontains=author_id)
        if parent_post_id:
            posts = posts.filter(parent_post_id=parent_post_id)
            
        return posts

    def resolve_post(self, info, id):
        try:
            return Post.objects.get(pk=id)
        except Post.DoesNotExist:
            raise GraphQLError(f"Пост с ID {id} не найден")

    def resolve_user_posts(self, info, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return Post.objects.filter(username=user.username).order_by("-timestamp")
        except User.DoesNotExist:
            raise GraphQLError(f"Пользователь с ID {user_id} не найден")

    def resolve_posts_connection(self, info, **kwargs):
        return Post.objects.all().order_by("-timestamp")

    def resolve_post_comments(self, info, post_id):
        try:
            Post.objects.get(pk=post_id)
            return Post.objects.filter(parent_post_id=post_id).order_by("timestamp")
        except Post.DoesNotExist:
            raise GraphQLError(f"Пост с ID {post_id} не найден")

    def resolve_search_posts(self, info, query):
        if not query or len(query.strip()) < 2:
            raise GraphQLError("Поисковый запрос должен содержать минимум 2 символа")
        
        return Post.objects.filter(
            Q(text__icontains=query) |
            Q(username__icontains=query)
        ).order_by("-timestamp")

    def resolve_search_users(self, info, query):
        if not query or len(query.strip()) < 2:
            raise GraphQLError("Поисковый запрос должен содержать минимум 2 символа")
        
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    def resolve_me(self, info):
        user = get_user_from_context(info)
        if not user:
            raise GraphQLError("Требуется аутентификация")
        return user
    
    def resolve_elasticsearch_search(self, info, query=None, size=20, from_=0, filters=None):
        try:
            from posts.search_service import post_search_service
            result = post_search_service.search_posts(query, size, from_, filters)
            
            if "error" in result:
                raise GraphQLError(result["error"])
            
            return result
        except Exception as e:
            raise GraphQLError(f"Ошибка поиска: {str(e)}")
    
    def resolve_search_suggestions(self, info, query):
        try:
            from posts.search_service import post_search_service
            return post_search_service.suggest_posts(query)
        except Exception as e:
            raise GraphQLError(f"Ошибка автодополнения: {str(e)}")
    
    def resolve_search_statistics(self, info):
        try:
            from posts.search_service import post_search_service
            return post_search_service.get_search_statistics()
        except Exception as e:
            raise GraphQLError(f"Ошибка получения статистики: {str(e)}")


class PostInput(graphene.InputObjectType):
    text = graphene.String(required=True)
    parent_post_id = graphene.ID()

class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    first_name = graphene.String()
    last_name = graphene.String()

class UserUpdateInput(graphene.InputObjectType):
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()

class LoginInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    password = graphene.String(required=True)


class CreatePost(graphene.Mutation):
    class Arguments:
        input = PostInput(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()

    @require_auth
    def mutate(self, info, input):
        user = get_user_from_context(info)
        
        if input.parent_post_id:
            try:
                parent_post = Post.objects.get(pk=input.parent_post_id)
            except Post.DoesNotExist:
                raise GraphQLError(f"Родительский пост с ID {input.parent_post_id} не найден")
        else:
            parent_post = None
        
        if not input.text or len(input.text.strip()) < 1:
            raise GraphQLError("Текст поста не может быть пустым")
        
        post = Post.objects.create(
            text=input.text.strip(),
            username=user.username,
            email=user.email,
            parent_post=parent_post
        )
        return CreatePost(post=post, success=True)

class UpdatePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = PostInput(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()

    @require_auth
    def mutate(self, info, id, input):
        user = get_user_from_context(info)
        
        try:
            post = Post.objects.get(pk=id)
        except Post.DoesNotExist:
            raise GraphQLError(f"Пост с ID {id} не найден")

        if post.username != user.username and not user.is_staff:
            raise GraphQLError("У вас нет прав для редактирования этого поста")
        
        if not input.text or len(input.text.strip()) < 1:
            raise GraphQLError("Текст поста не может быть пустым")
        
        post.text = input.text.strip()
        
        if input.parent_post_id:
            try:
                parent_post = Post.objects.get(pk=input.parent_post_id)
                post.parent_post = parent_post
            except Post.DoesNotExist:
                raise GraphQLError(f"Родительский пост с ID {input.parent_post_id} не найден")
        
        post.save()
        return UpdatePost(post=post, success=True)

class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @require_auth
    def mutate(self, info, id):
        user = get_user_from_context(info)
        
        try:
            post = Post.objects.get(pk=id)
        except Post.DoesNotExist:
            raise GraphQLError(f"Пост с ID {id} не найден")

        if post.username != user.username and not user.is_staff:
            raise GraphQLError("У вас нет прав для удаления этого поста")
        
        post.delete()
        return DeletePost(success=True)

class CreateUser(graphene.Mutation):
    class Arguments:
        input = UserInput(required=True)

    user = graphene.Field(UserType)
    success = graphene.Boolean()

    def mutate(self, info, input):
        if not input.username or len(input.username.strip()) < 3:
            raise GraphQLError("Имя пользователя должно содержать минимум 3 символа")
        
        if not input.email or "@" not in input.email:
            raise GraphQLError("Некорректный email адрес")
        
        if not input.password or len(input.password) < 6:
            raise GraphQLError("Пароль должен содержать минимум 6 символов")

        if User.objects.filter(username=input.username).exists():
            raise GraphQLError("Пользователь с таким именем уже существует")
        
        if User.objects.filter(email=input.email).exists():
            raise GraphQLError("Пользователь с таким email уже существует")
        
        try:
            user = User.objects.create_user(
                username=input.username.strip(),
                email=input.email.strip(),
                password=input.password,
                first_name=input.first_name.strip() if input.first_name else "",
                last_name=input.last_name.strip() if input.last_name else ""
            )
            return CreateUser(user=user, success=True)
        except Exception as e:
            raise GraphQLError(f"Ошибка при создании пользователя: {str(e)}")

class UpdateUser(graphene.Mutation):
    class Arguments:
        input = UserUpdateInput(required=True)

    user = graphene.Field(AuthenticatedUserType)
    success = graphene.Boolean()

    @require_auth
    def mutate(self, info, input):
        user = get_user_from_context(info)

        if input.username and len(input.username.strip()) < 3:
            raise GraphQLError("Имя пользователя должно содержать минимум 3 символа")
        
        if input.email and "@" not in input.email:
            raise GraphQLError("Некорректный email адрес")

        if input.username and User.objects.filter(username=input.username).exclude(pk=user.id).exists():
            raise GraphQLError("Пользователь с таким именем уже существует")
        
        if input.email and User.objects.filter(email=input.email).exclude(pk=user.id).exists():
            raise GraphQLError("Пользователь с таким email уже существует")
        
        if input.username:
            user.username = input.username.strip()
        if input.email:
            user.email = input.email.strip()
        if input.first_name is not None:
            user.first_name = input.first_name.strip() if input.first_name else ""
        if input.last_name is not None:
            user.last_name = input.last_name.strip() if input.last_name else ""
        
        user.save()
        return UpdateUser(user=user, success=True)

class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @require_auth
    def mutate(self, info, id):
        user = get_user_from_context(info)
        
        try:
            target_user = User.objects.get(pk=id)
        except User.DoesNotExist:
            raise GraphQLError(f"Пользователь с ID {id} не найден")

        if target_user.id != user.id and not user.is_staff:
            raise GraphQLError("У вас нет прав для удаления этого пользователя")

        if target_user.is_superuser:
            raise GraphQLError("Нельзя удалить суперпользователя")
        
        target_user.delete()
        return DeleteUser(success=True)

class Login(graphene.Mutation):
    class Arguments:
        input = LoginInput(required=True)

    token = graphene.String()
    user = graphene.Field(AuthenticatedUserType)
    success = graphene.Boolean()

    def mutate(self, info, input):
        if not input.username or not input.password:
            raise GraphQLError("Имя пользователя и пароль обязательны")
        
        try:
            from django.contrib.auth import authenticate
            user = authenticate(username=input.username, password=input.password)
            if user:
                token = create_jwt_token(user)
                return Login(
                    token=token,
                    user=user,
                    success=True
                )
            else:
                raise GraphQLError("Неверные учетные данные")
        except GraphQLError:
            raise
        except Exception as e:
            raise GraphQLError(f"Ошибка аутентификации: {str(e)}")

class Logout(graphene.Mutation):
    success = graphene.Boolean()

    @require_auth
    def mutate(self, info):
        return Logout(success=True)


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()

    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

    login = Login.Field()
    logout = Logout.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
