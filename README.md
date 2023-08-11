Foodgram

### Описание:

*Проект Foodgram «Продуктовый помощник» позволяет пользователи публиковать рецепты,
подписываться на публикации других пользователей, добавлять понравившиеся рецепты
в список «Избранное», а перед походом в магазин скачивать сводный список продуктов,
необходимых для приготовления выбранных блюд.
*


### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Sashkina/foodgram-project-react.git
```

```
cd backend
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

### Примеры:

1. **Получение списка всех рецептов**

**Request sample:**
GET api/recipes/

**Response sample:**
{
    "id": 0,
    "tags": [
        + {...}
    ],
    "author": {},
    "ingredients": [
        + {...}
    ],
    "is_favorited": true,
    "is_in_shopping_cart": true,
    "name": "string",
    "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
    "text": "string",
    "cooking_time": 1
}

2. **Добавление рецепта в список покупок**

**Request sample:**
POST /api/recipes/{id}/shopping_cart/

**Response sample:**
{
    "id": 0,
    "name": "string",
    "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
    "cooking_time": 1
}
