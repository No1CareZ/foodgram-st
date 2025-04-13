import io
import datetime

from rest_framework import filters, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.http import FileResponse
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, reverse
from djoser import views
from django_filters import rest_framework


from recipes.models import Ingredient
from recipes.models import SubPair, Recipe, ToBuyList, \
    Favorite

from .serializers import IngredientSerializer, AvatarSerializer, \
    SubscriberSerializer, CreateRecipeSerializer, RecipeSerializer, \
    CutRecipeSerializer
from .permissions import IsAuthorOrReadOnlyPermission


User = get_user_model()


class UserViewSet(views.UserViewSet):
    """
    CRUD allowing viewset for User.
    """
    permission_classes = (IsAuthorOrReadOnlyPermission, )

    page_size_query_param = ('limit',)

    queryset = User.objects.all()

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def avatar(self, request):
        """
        Avatar connected actions.
        """
        user = request.user
        if request.method == 'PUT':
            if request.data.get('avatar'):
                serializer = AvatarSerializer(
                    user,
                    data=request.data,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        serializer.data,
                        status=status.HTTP_200_OK
                    )
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            user.avatar = None
            user.save()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_me(self, request):
        """
        Get profile of user. Unauthenticated user will recive 401.
        """
        return super().me(request)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Get subscribed pages.
        """
        targets = request.user.subscriber.values('contentmaker')
        queryset = self.get_queryset().filter(
            id__in=targets
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriberSerializer(
            pages, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """
        Subscribe/Unsubscribe.
        """
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = SubPair.objects.filter(
            subscriber=user,
            contentmaker=author
        )
        if request.method == 'POST':
            if user == author:
                raise ValidationError(
                    'Вы не можете подписаться сами на себя!'
                )
            if subscription.exists():
                raise ValidationError(
                    'Вы уже подписаны на этого пользователя!'
                )
            SubPair.objects.create(
                subscriber=user,
                contentmaker=author
            )
            serializer = SubscriberSerializer(
                author,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            subpairsearch = SubPair.objects.all()\
                .filter(subscriber=user)\
                .filter(contentmaker=author)

            if subpairsearch:
                subpairsearch[0].delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    page_size_query_param = ('limit',)

    queryset = Recipe.objects.all()

    filter_backends = (
        rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    search_fields = ('=author', 'is_favorited', 'is_in_shopping_cart')

    def get_queryset(self):
        queryset = super().get_queryset()
        author = self.request.query_params.get(
            'author'
        )
        is_favorited = self.request.query_params.get(
            'is_favorited'
        )
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )

        if author:
            queryset = queryset.filter(author=author)
        if is_favorited and self.request.user.is_authenticated:
            queryset = queryset.filter(fav__user=self.request.user)
        if is_in_shopping_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(buylist__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return CreateRecipeSerializer
        else:
            return RecipeSerializer

    def get_permissions(self):
        if self.action == 'create' or self.action == 'partial_update':
            permission_classes = (
                permissions.IsAuthenticated,
                IsAuthorOrReadOnlyPermission
            )
        else:
            permission_classes = (IsAuthorOrReadOnlyPermission, )
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    def actions_recipe(self, request, pk, model, error_message):
        if not request.user.is_authenticated:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED
            )

        recipe = get_object_or_404(
            Recipe,
            pk=pk
        )

        if request.method == 'POST':
            collection, created = model.objects.get_or_create(
                user=request.user,
                recipes=recipe,
            )

            if created:
                return Response(
                    CutRecipeSerializer(recipe).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'Fail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        get_object_or_404(
            model,
            user=request.user,
            recipes=pk
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        ###################
        if request.method == 'DELETE' and request.user.is_authenticated:
            is_in_fav = Favorite.objects.all()\
                .filter(recipes__pk=pk)\
                .filter(user=request.user)
            is_exsists = Recipe.objects.filter(pk=pk).exists()

            if not is_in_fav and is_exsists:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )

        return self.actions_recipe(
            request,
            pk,
            Favorite,
            'Рецепт уже был избран!'
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'DELETE' and request.user.is_authenticated:
            is_in_cart = ToBuyList.objects.all()\
                .filter(recipes__pk=pk)\
                .filter(user=request.user)
            is_exsists = Recipe.objects.filter(pk=pk).exists()

            if not is_in_cart and is_exsists:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
        return self.actions_recipe(
            request,
            pk,
            ToBuyList,
            'Рецепт уже в корзине'
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = ToBuyList.objects.filter(
            user=request.user
        ).values(
            'recipes__recipe_ingredient__ingredient__name',
            'recipes__recipe_ingredient__ingredient__measurement_unit'
        ).annotate(
            total=Sum('recipes__recipe_ingredient__amount')
        ).order_by(
            'recipes__recipe_ingredient__ingredient__name'
        )

        recipes = request.user.buylist.all()

        file_head = (
            f'Список покупок {request.user.username}'
            + f' ({datetime.datetime.now()}) - \n'
        )

        file_ingredients = (
            'Ингридиенты:\n'
            + '\n'.join(
                f'''{i}. {ingredient[
                    'recipes__recipe_ingredient__ingredient__name'
                ].capitalize()} '''
                f'''({ingredient[
                    'recipes__recipe_ingredient__ingredient__measurement_unit'
                ]})'''
                f''' - {ingredient['total']}'''
                for i, ingredient in enumerate(ingredients, start=1)
            )
        )

        file_recipes = (
            'Рецепты:\n'
            + '\n'.join(
                f'''{i}. {recipe.recipes.name} от '''
                f'''{recipe.recipes.author}'''
                for i, recipe in enumerate(recipes, start=1)
            )
        )

        file_content = '\n'.join([
            file_head,
            file_ingredients,
            file_recipes
        ])

        file_content = io.BytesIO(file_content.encode('utf-8'))

        return FileResponse(
            file_content,
            as_attachment=True,
            filename='shopping-list.txt',
            content_type='text/plain',
        )

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        url_name='get-link',
    )
    def return_short_link(self, request, pk):
        """
        Return short link for recipe.
        """
        get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse(
                'api:recipes-detail',
                kwargs={'pk': pk}
            )
        )
        return Response({'short-link': short_link})


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    CRUD allowing viewset for Ingridents.
    """
    permission_classes = (permissions.AllowAny,)

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    filter_backends = (filters.SearchFilter,)
    search_fields = ('=name',)

    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset
