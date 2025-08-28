"""
JWT utilities for GraphQL authentication
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token, get_user
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
        user = get_user(token)
        return user
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
