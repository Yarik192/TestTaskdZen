from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from posts.forms import PostForm
from posts.models import Post


class PostsView(LoginRequiredMixin, FormMixin, ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 25
    template_name = "index.html"
    form_class = PostForm

    success_url = reverse_lazy("posts")
    login_url = reverse_lazy("login")
    redirect_field_name = "next"


    def get_queryset(self):
        queryset = super().get_queryset()
        
        sort_by = self.request.GET.get("sort_by", "timestamp")
        order = self.request.GET.get("order", "desc")
        
        if order == "asc":
            sort_prefix = ""
        else:
            sort_prefix = "-"
        
        if sort_by == "username":
            queryset = queryset.order_by(f"{sort_prefix}username")
        elif sort_by == "email":
            queryset = queryset.order_by(f"{sort_prefix}email")
        elif sort_by == "timestamp":
            queryset = queryset.order_by(f"{sort_prefix}timestamp")
        else:
            queryset = queryset.order_by("-timestamp")
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in context:
            context["form"] = self.get_form()

        context["current_sort"] = self.request.GET.get("sort_by", "timestamp")
        context["current_order"] = self.request.GET.get("order", "desc")

        posts = context.get("posts", [])
        final_list = []

        root_posts = [post for post in posts if post.parent_post is None]
        
        def add_post_with_children(post, level=0):
            post.level = level
            children = Post.objects.filter(parent_post=post).order_by("timestamp")
            post.has_answer_btn = children.count() == 0
            
            final_list.append(post)
            
            for child in children:
                add_post_with_children(child, level + 2)
        
        for root_post in root_posts:
            add_post_with_children(root_post)

        context["posts"] = final_list
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form_class()(request.POST, request.FILES)
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


