from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from posts.views import PostsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", PostsView.as_view(), name="posts"),
    path("", include("users.urls")),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]


if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
