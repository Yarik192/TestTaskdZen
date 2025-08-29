# Система комментариев с сортировкой

## Описание
Веб-приложение для создания и управления комментариями с возможностью сортировки по различным критериям.

## Функциональность

### Сортировка постов
- **По имени пользователя** (`username`) - алфавитная сортировка
- **По email** (`email`) - алфавитная сортировка  
- **По дате добавления** (`timestamp`) - хронологическая сортировка

### Направления сортировки
- **По убыванию** (`desc`) - от большего к меньшему
- **По возрастанию** (`asc`) - от меньшего к большему

### Сортировка по умолчанию
- **LIFO** (Last In, First Out) - новые посты отображаются первыми

### GraphQL API
- **Полнотекстовый поиск** по постам и комментариям
- **Elasticsearch интеграция** для быстрого поиска
- **Аутентификация** через JWT токены
- **CRUD операции** для постов и пользователей
- **Пагинация** и фильтрация результатов

## Технологии
- Django 5.2.4
- GraphQL (graphene-django)
- Elasticsearch 8.11.0
- Apache Kafka 7.4.0
- Bootstrap 5.3.0
- Bootstrap Icons 1.11.0
- Python 3.11+
- SQLite 3
- Docker & Docker Compose

## Установка и запуск

### 🐳 Запуск в Docker (рекомендуется)

**Просто запустите:**
```bash
docker-compose up -d
```

**Откройте в браузере:**
- Django: http://localhost:8000
- GraphQL Playground: http://localhost:8000/graphql/
- Elasticsearch: http://localhost:9200
- Kafka UI: http://localhost:8080

## GraphQL API

### Основные эндпоинты
- **GraphQL Playground**: http://localhost:8000/graphql/

### Примеры запросов

#### Получение всех постов
```graphql
query {
  allPosts {
    id
    text
    username
    email
    timestamp
    parentPost {
      id
      text
    }
  }
}
```

#### Поиск постов
```graphql
query {
  elasticsearchSearch(query: "поисковый запрос", size: 10) {
    hits {
      id
      text
      username
      score
    }
    total
  }
}
```

#### Создание поста
```graphql
mutation {
  createPost(input: {
    text: "Текст нового поста"
    parentPostId: "1"
  }) {
    post {
      id
      text
      username
    }
    success
  }
}
```

#### Получение всех постов
```graphql
query {
  allPosts {
    id
    text
    username
    email
    timestamp
    parentPost {
      id
      text
    }
  }
}
```

#### Поиск постов
```graphql
query {
  elasticsearchSearch(query: "поисковый запрос", size: 10) {
    hits {
      id
      text
      username
      score
    }
    total
  }
}
```
### Компоненты системы
- **Django** - основной веб-фреймворк
- **GraphQL** - API для гибкого взаимодействия с данными
- **Elasticsearch** - поисковая система для быстрого поиска
- **Kafka** - система обмена сообщениями для асинхронной обработки
- **JWT** - аутентификация пользователей

#### Создание поста
```graphql
mutation {
  createPost(input: {
    text: "Текст нового поста"
    parentPostId: "1"
  }) {
    post {
      id
      text
      username
    }
    success
  }
}
```

### Аутентификация
API использует JWT токены. Для авторизованных запросов добавьте заголовок:
```
Authorization: JWT <your_token>
```

## Архитектура

### Компоненты системы
- **Django** - основной веб-фреймворк
- **GraphQL** - API для гибкого взаимодействия с данными
- **Elasticsearch** - поисковая система для быстрого поиска
- **Kafka** - система обмена сообщениями для асинхронной обработки
- **JWT** - аутентификация пользователей

### Поток данных
1. Пользователь создает пост через GraphQL API
2. Django сохраняет пост в базе данных
3. Kafka отправляет событие о новом посте
4. Elasticsearch индексирует пост для поиска
5. Пост становится доступен для поиска через API

## Структура проекта
```
test_task_comments/
├── posts/           # Приложение для постов
│   ├── documents.py # Elasticsearch документы
│   ├── search_service.py # Поисковый сервис
│   └── signals.py   # Django сигналы
├── users/           # Приложение для пользователей
├── graphql_app/     # GraphQL API
│   ├── schema.py    # GraphQL схема
│   └── jwt_utils.py # JWT аутентификация
├── common/          # Общие компоненты
│   └── kafka_client.py # Kafka клиент
├── templates/       # HTML шаблоны
├── static/          # CSS, JS, изображения
├── media/           # Загружаемые файлы
└── docker-compose.yml
```

## Docker сервисы
- **django** - Django приложение
- **elasticsearch** - Поисковая система
- **kafka** - Apache Kafka брокер
- **zookeeper** - Координатор для Kafka
- **kafka-ui** - Веб-интерфейс для мониторинга Kafka
