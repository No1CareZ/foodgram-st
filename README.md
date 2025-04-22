# Foodgram
## О проекте
Это большая работа, выполняя которую вы были примены знания, полученные за время обучения на курсе Яндекс Практикум: Python бэкенд-разработчик.

## Описание 
«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

-- описание взято с курса Яндекс Практикум: Python бэкенд-разработчик
## Запуск
### Используя Docker
```bash
cd .\infra\
```
```bash
docker compose up
```
### Debug/No Docker
```bash
cd .\backend\
```
```bash
python manage.py makemigrations
```
```bash
python manage.py migrate
```
```bash
python manage.py populate_ingredients ingredients.json
```
```bash
python manage.py runserver
```

## Примеры запросов
```
GET /api/ingredients

[
  {
    "id": 0,
    "name": "Капуста",
    "measurement_unit": "кг"
  }
]
```
```
GET /api/users/subscriptions/

{
  "count": 123,
  "next": "http://foodgram.example.org/api/users/subscriptions/?page=4",
  "previous": "http://foodgram.example.org/api/users/subscriptions/?page=2",
  "results": [
    {
      "email": "user@example.com",
      "id": 0,
      "username": "string",
      "first_name": "Вася",
      "last_name": "Иванов",
      "is_subscribed": true,
      "recipes": [
        {
          "id": 0,
          "name": "string",
          "image": "http://foodgram.example.org/media/recipes/images/image.png",
          "cooking_time": 1
        }
      ],
      "recipes_count": 0,
      "avatar": "http://foodgram.example.org/media/users/image.png"
    }
  ]
}
```
```
GET /api/recipes/

{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

## Инструментарий
* `Django`
* `DRF`
* `Djoser`
* `Docker`
* `Gunicorn`
* `PostgreSQL`
* `Nginx`

## Автор

[Alex Survilov](https://github.com/No1CareZ)
