from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Post


@registry.register_document
class PostDocument(Document):
    username = fields.TextField()
    email = fields.EmailField()
    text = fields.TextField()
    timestamp = fields.DateField()
    parent_post_id = fields.IntegerField(attr="parent_post_id")
    
    class Index:
        name = "posts"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    
    class Django:
        model = Post
        fields = [
            "id",
        ]
        
        exclude = ["image", "text_file"]
    
    def get_queryset(self):
        return super().get_queryset()
    
    def get_indexing_queryset(self):
        return self.get_queryset().select_related("parent_post")
    
    @property
    def parent_post_id(self):
        if self.parent_post:
            return self.parent_post.id
        return None
