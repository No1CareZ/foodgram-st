from rest_framework.routers import SimpleRouter
from django.urls import include, path

from .views import UserViewSet, IngredientViewSet, RecipeViewSet

app_name = 'api'

simple_router = SimpleRouter()

simple_router.register(
    'users',
    UserViewSet,
    basename='users'
)
simple_router.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
simple_router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    path(
        '',
        include(simple_router.urls)
    ),
    path(
        'auth/',
        include('djoser.urls.authtoken')
    ),
]
