import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token
from graphql import GraphQLError

User = get_user_model()

def create_jwt_token(user):
    try:
        token = get_token(user)
        return token
    except Exception as e:
        raise GraphQLError(f"Ошибка создания токена: {str(e)}")

def verify_jwt_token(token):
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=['HS256']
        )
        user_id = payload.get('user_id')
        if user_id:
            return User.objects.get(id=user_id)
        return None
    except jwt.ExpiredSignatureError:
        raise GraphQLError("Токен истек")
    except jwt.InvalidTokenError:
        raise GraphQLError("Неверный токен")
    except User.DoesNotExist:
        raise GraphQLError("Пользователь не найден")
    except Exception as e:
        raise GraphQLError(f"Ошибка проверки токена: {str(e)}")

def get_user_from_context(info):
    if info.context.user.is_authenticated:
        return info.context.user
    return None

def require_auth(func):
    def wrapper(self, info, *args, **kwargs):
        user = get_user_from_context(info)
        if not user:
            raise GraphQLError("Требуется аутентификация")
        return func(self, info, *args, **kwargs)
    return wrapper
