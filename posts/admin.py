from django.contrib import admin

from posts.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("username", "elide_text", "parent_post")

    def elide_text(self, obj):
        return f"{obj.text[:64]}..."
