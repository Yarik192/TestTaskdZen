from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from posts.forms import PostForm
from posts.models import Post


class PostsView(FormMixin, ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 25
    template_name = "index.html"
    form_class = PostForm
    success_url = reverse_lazy("posts")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in context:
            context["form"] = self.get_form()

        posts = context.get("posts", [])
        final_list = []

        for post in posts:
            if post.parent_post is None:
                level = 0
                current = post
                while current:
                    current.level = level
                    child = getattr(current, "child", None)
                    current.has_answer_btn = child is None
                    final_list.append(current)

                    current = child
                    level += 2

        context["posts"] = final_list
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            user = request.user
            instance = form.save(commit=False)
            instance.username = user.username
            instance.email = user.email

            parent_post_id = request.POST.get("parent_post_id")
            if parent_post_id:
                try:
                    parent_post = Post.objects.get(id=parent_post_id)
                    instance.parent_post = parent_post
                except Post.DoesNotExist:
                    pass

            instance.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


