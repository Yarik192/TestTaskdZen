from elasticsearch import Elasticsearch
from django.conf import settings
from django_elasticsearch_dsl.search import Search
from .documents import PostDocument
from common.kafka_client import KafkaProducer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PostSearchService:
    def __init__(self):
        self.es_client = Elasticsearch([f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"])
        self.kafka_producer = KafkaProducer()
    
    def search_posts(self, query, size=20, from_=0, filters=None):
        try:
            search = PostDocument.search()
            
            if query:
                search = search.query(
                    "multi_match",
                    query=query,
                    fields=["text^3", "username^2", "email"],
                    fuzziness="AUTO"
                )
            
            if filters:
                if filters.get("username"):
                    search = search.filter("term", username=filters["username"])
                if filters.get("date_from"):
                    search = search.filter("range", timestamp={"gte": filters["date_from"]})
                if filters.get("date_to"):
                    search = search.filter("range", timestamp={"lte": filters["date_to"]})
                if filters.get("parent_post_id"):
                    search = search.filter("term", parent_post_id=filters["parent_post_id"])

            search.aggs.bucket("usernames", "terms", field="username", size=10)
            search.aggs.bucket("dates", "date_histogram", field="timestamp", interval="day")

            response = search[from_:from_ + size].execute()

            self._log_search_query(query, filters, len(response.hits))
            
            return {
                "hits": [hit.to_dict() for hit in response.hits],
                "total": response.hits.total.value,
                "aggregations": response.aggregations.to_dict(),
                "query": query,
                "filters": filters
            }
            
        except Exception as e:
            logger.error(f"Ошибка поиска в Elasticsearch: {e}")
            return {"error": str(e), "hits": [], "total": 0}
    
    def suggest_posts(self, query, size=5):
        try:
            search = PostDocument.search()
            search = search.suggest("suggestions", query, {
                "completion": {
                    "field": "text",
                    "size": size,
                    "skip_duplicates": True
                }
            })
            
            response = search.execute()
            suggestions = []
            
            if hasattr(response, "suggest") and "suggestions" in response.suggest:
                for suggestion in response.suggest.suggestions:
                    for option in suggestion.options:
                        suggestions.append(option.text)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Ошибка автодополнения: {e}")
            return []
    
    def index_post(self, post):
        try:
            PostDocument.update(post)
            logger.info(f"Пост {post.id} проиндексирован в Elasticsearch")
        except Exception as e:
            logger.error(f"Ошибка индексации поста {post.id}: {e}")
    
    def remove_post(self, post_id):
        try:
            PostDocument.get(id=post_id).delete()
            logger.info(f"Пост {post_id} удален из Elasticsearch")
        except Exception as e:
            logger.error(f"Ошибка удаления поста {post_id}: {e}")
    
    def _log_search_query(self, query, filters, results_count):
        try:
            search_log = {
                "type": "search_query",
                "query": query,
                "filters": filters,
                "results_count": results_count,
                "timestamp": str(datetime.now())
            }
            
            self.kafka_producer.send_message(
                topic=settings.KAFKA_POSTS_TOPIC,
                message=search_log
            )
        except Exception as e:
            logger.error(f"Ошибка логирования поискового запроса в Kafka: {e}")
    
    def get_search_statistics(self):
        try:
            search = PostDocument.search()
            search = search.aggs.bucket("total_posts", "value_count", field="id")
            search = search.aggs.bucket("unique_users", "cardinality", field="username")
            search = search.aggs.bucket("posts_by_date", "date_histogram", field="timestamp", interval="day")
            
            response = search.execute()
            
            return {
                "total_posts": response.aggregations.total_posts.value,
                "unique_users": response.aggregations.unique_users.value,
                "posts_by_date": response.aggregations.posts_by_date.buckets
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}


post_search_service = PostSearchService()
