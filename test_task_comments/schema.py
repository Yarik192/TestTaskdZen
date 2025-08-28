import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from posts.models import Post
from users.models import Profile

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')

class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = '__all__'

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'

# Query
class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    all_posts = graphene.List(PostType)
    post = graphene.Field(PostType, id=graphene.ID(required=True))
    user_posts = graphene.List(PostType, user_id=graphene.ID(required=True))
    posts_paginated = graphene.List(PostType, first=graphene.Int(), skip=graphene.Int())

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_user(self, info, id):
        return User.objects.get(pk=id)

    def resolve_all_posts(self, info):
        return Post.objects.all().order_by('-created_at')

    def resolve_post(self, info, id):
        return Post.objects.get(pk=id)

    def resolve_user_posts(self, info, user_id):
        return Post.objects.filter(author_id=user_id).order_by('-created_at')

    def resolve_posts_paginated(self, info, first=None, skip=None):
        posts = Post.objects.all().order_by('-created_at')
        if skip:
            posts = posts[skip:]
        if first:
            posts = posts[:first]
        return posts


class CreatePost(graphene.Mutation):
    class Arguments:
        text = graphene.String(required=True)
        author_id = graphene.ID(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, text, author_id):
        try:
            author = User.objects.get(pk=author_id)
            post = Post.objects.create(
                text=text,
                author=author
            )
            return CreatePost(post=post, success=True, message="Пост успешно создан")
        except Exception as e:
            return CreatePost(post=None, success=False, message=str(e))


class UpdatePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        text = graphene.String(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, text):
        try:
            post = Post.objects.get(pk=id)
            post.text = text
            post.save()
            return UpdatePost(post=post, success=True, message="Пост успешно обновлен")
        except Exception as e:
            return UpdatePost(post=None, success=False, message=str(e))


class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            post = Post.objects.get(pk=id)
            post.delete()
            return DeletePost(success=True, message="Пост успешно удален")
        except Exception as e:
            return DeletePost(success=False, message=str(e))


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, username, email, password, first_name="", last_name=""):
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            return CreateUser(user=user, success=True, message="Пользователь успешно создан")
        except Exception as e:
            return CreateUser(user=None, success=False, message=str(e))


class ObtainJSONWebToken(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, username, password):
        try:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user:
                from graphql_jwt.shortcuts import create_refresh_token, get_token
                token = get_token(user)
                return ObtainJSONWebToken(token=token, success=True, message="Успешная аутентификация")
            else:
                return ObtainJSONWebToken(token=None, success=False, message="Неверные учетные данные")
        except Exception as e:
            return ObtainJSONWebToken(token=None, success=False, message=str(e))


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    create_user = CreateUser.Field()
    obtain_jwt_token = ObtainJSONWebToken.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
