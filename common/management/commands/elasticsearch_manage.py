from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.management.commands import search_index_command
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Управление Elasticsearch индексами"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["create", "delete", "rebuild", "update"],
            help="Действие для выполнения"
        )
        parser.add_argument(
            "--models",
            nargs="+",
            help="Список моделей для обработки"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Принудительное выполнение"
        )

    def handle(self, *args, **options):
        action = options["action"]
        models = options["models"]
        force = options["force"]

        self.stdout.write(f"Выполняю действие: {action}")

        try:
            if action == "create":
                self.create_indexes(models, force)
            elif action == "delete":
                self.delete_indexes(models, force)
            elif action == "rebuild":
                self.rebuild_indexes(models, force)
            elif action == "update":
                self.update_indexes(models, force)

            self.stdout.write(
                self.style.SUCCESS(f"Действие \"{action}\" выполнено успешно")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при выполнении действия \"{action}\": {e}")
            )
            logger.error(f"Ошибка Elasticsearch команды: {e}")

    def create_indexes(self, models, force):
        from django_elasticsearch_dsl.registries import registry
        
        if models:
            for model in models:
                if model in registry._models:
                    self.stdout.write(f"Создаю индекс для модели: {model}")
                    registry._models[model].create_index()
                else:
                    self.stdout.write(f"Модель {model} не найдена в registry")
        else:
            self.stdout.write("Создаю все индексы...")
            search_index_command.Command().handle(action="create")

    def delete_indexes(self, models, force):
        if not force:
            self.stdout.write(
                self.style.WARNING("Используйте --force для подтверждения удаления")
            )
            return

        from django_elasticsearch_dsl.registries import registry
        
        if models:
            for model in models:
                if model in registry._models:
                    self.stdout.write(f"Удаляю индекс для модели: {model}")
                    registry._models[model].delete_index()
                else:
                    self.stdout.write(f"Модель {model} не найдена в registry")
        else:
            self.stdout.write("Удаляю все индексы...")
            search_index_command.Command().handle(action="delete")

    def rebuild_indexes(self, models, force):
        self.stdout.write("Пересоздаю индексы...")
        self.delete_indexes(models, True)
        self.create_indexes(models, force)
        
        if not models:
            self.stdout.write("Обновляю данные...")
            search_index_command.Command().handle(action="update")

    def update_indexes(self, models, force):
        self.stdout.write("Обновляю данные в индексах...")
        search_index_command.Command().handle(action="update")
