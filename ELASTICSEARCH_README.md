# Elasticsearch интеграция в Django проект

## Описание

Этот проект интегрирован с Elasticsearch для полнотекстового поиска по постам. Интеграция включает:

- Автоматическую индексацию постов при создании/обновлении/удалении
- GraphQL API для поиска
- Интеграцию с Kafka для логирования поисковых запросов
- Автодополнение и агрегации

## Установка и настройка

### 1. Зависимости

Установите необходимые пакеты:

```bash
pip install -r requirements.txt
```

### 2. Запуск Elasticsearch

Запустите Elasticsearch и Kibana через Docker Compose:

```bash
docker-compose up -d elasticsearch kibana
```

Или запустите все сервисы (включая Kafka):

```bash
docker-compose up -d
```

### 3. Создание индексов

Создайте индексы Elasticsearch:

```bash
python manage.py elasticsearch_manage create
```

### 4. Настройка переменных окружения

Добавьте в `.env` файл:

```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX_PREFIX=test_task_comments
```

## Использование

### GraphQL API

#### Поиск постов

```graphql
query SearchPosts($query: String, $size: Int, $from: Int, $filters: JSONString) {
  elasticsearchSearch(query: $query, size: $size, from: $from, filters: $filters) {
    hits {
      id
      username
      email
      text
      timestamp
      parentPostId
      score
    }
    total
    aggregations {
      usernames
      dates
    }
    query
    filters
  }
}
```

#### Автодополнение

```graphql
query GetSuggestions($query: String!) {
  searchSuggestions(query: $query)
}
```

#### Статистика поиска

```graphql
query GetSearchStatistics {
  searchStatistics {
    totalPosts
    uniqueUsers
    postsByDate
  }
}
```

### Фильтры поиска

Поддерживаемые фильтры:

```json
{
  "username": "имя_пользователя",
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "parent_post_id": 123
}
```

## Команды управления

### Создание индексов

```bash
python manage.py elasticsearch_manage create
```

### Удаление индексов

```bash
python manage.py elasticsearch_manage delete --force
```

### Пересоздание индексов

```bash
python manage.py elasticsearch_manage rebuild
```

### Обновление данных

```bash
python manage.py elasticsearch_manage update
```

## Архитектура

### Компоненты

1. **PostDocument** (`posts/documents.py`) - Определение схемы индекса Elasticsearch
2. **PostSearchService** (`posts/search_service.py`) - Сервис для работы с поиском
3. **GraphQL схема** (`graphql_app/schema.py`) - API для поиска
4. **Модель Post** (`posts/models.py`) - Автоматическая индексация

### Автоматическая индексация

Посты автоматически индексируются в Elasticsearch при:
- Создании нового поста
- Обновлении существующего поста
- Удалении поста

### Интеграция с Kafka

Все поисковые запросы логируются в Kafka для аналитики:
- Поисковый запрос
- Примененные фильтры
- Количество результатов
- Временная метка

## Мониторинг

### Kibana

Откройте Kibana по адресу: http://localhost:5601

### Elasticsearch API

Проверьте статус Elasticsearch: http://localhost:9200

### Логи Django

Поисковые запросы логируются в Django логах и отправляются в Kafka.

## Производительность

### Оптимизации

- Использование `select_related` для уменьшения количества запросов
- Настройка количества шардов и реплик
- Кэширование результатов поиска

### Мониторинг

- Отслеживание времени выполнения поиска
- Мониторинг размера индексов
- Анализ популярных поисковых запросов

## Troubleshooting

### Проблемы с подключением

1. Проверьте, что Elasticsearch запущен: `curl http://localhost:9200`
2. Убедитесь, что порты не заблокированы
3. Проверьте настройки в `.env` файле

### Проблемы с индексацией

1. Проверьте логи Django
2. Убедитесь, что индексы созданы
3. Проверьте права доступа к Elasticsearch

### Проблемы с поиском

1. Проверьте синтаксис GraphQL запросов
2. Убедитесь, что данные проиндексированы
3. Проверьте логи Elasticsearch

## Разработка

### Добавление новых полей

1. Обновите модель `Post`
2. Обновите `PostDocument`
3. Пересоздайте индексы
4. Обновите GraphQL схему

### Кастомные анализаторы

Добавьте в `PostDocument`:

```python
class Index:
    name = 'posts'
    settings = {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'analysis': {
            'analyzer': {
                'russian_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'russian_stop', 'russian_stemmer']
                }
            }
        }
    }
```
