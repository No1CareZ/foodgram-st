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
