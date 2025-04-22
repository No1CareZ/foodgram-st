import datetime
import io

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, reverse
from django_filters import rest_framework
from djoser import views
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnlyPermission
from api.serializers import (AvatarSerializer, CreateRecipeSerializer,
                             CutRecipeSerializer, IngredientSerializer,
                             RecipeSerializer, SubscriberSerializer)
from recipes.models import Favorite, Ingredient, Recipe, SubPair, ToBuyList

User = get_user_model()


class UserViewSet(views.UserViewSet):
    """
    CRUD allowing viewset for User.
    """

    permission_classes = (IsAuthorOrReadOnlyPermission,)

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
            if not request.data.get('avatar'):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

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

        queryset = self.get_queryset().filter(
            subscribers__subscriber=request.user
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
            content_maker=author
        )
        if request.method == 'POST':
            if user == author:
                raise ValidationError(
                    'You cannot subscribe to yourself!'
                )
            if subscription.exists():
                raise ValidationError(
                    'You are already subscribed to this user!'
                )
            SubPair.objects.create(
                subscriber=user,
                content_maker=author
            )
            serializer = SubscriberSerializer(
                author,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        subpairsearch = (
            SubPair.objects.all()
            .filter(subscriber=user)
            .filter(content_maker=author)
        )
        if subpairsearch:
            subpairsearch[0].delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnlyPermission,
    )

    page_size_query_param = ('limit',)

    queryset = Recipe.objects.all()

    filter_backends = (
        rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action not in SAFE_METHODS:
            return CreateRecipeSerializer
        return RecipeSerializer

    def actions_recipe(self, request, pk, model, error_message):
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

    def _fav_and_cart(self, request, pk, model, error_message):
        if self.request.method == 'DELETE':
            is_in_model = model.objects.filter(
                recipes__pk=pk,
                user=request.user
            ).exists()
            is_exsists = Recipe.objects.filter(pk=pk).exists()

            if not is_in_model and is_exsists:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
        return self.actions_recipe(
            request,
            pk,
            model,
            error_message
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self._fav_and_cart(
            request,
            pk,
            Favorite,
            'Recipe was already favorited!'
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self._fav_and_cart(
            request,
            pk,
            ToBuyList,
            'Recipe is already in the cart!'
        )

    def _download_file(self, request, ingredients):
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

        file_content = '\n'.join([
            file_head,
            file_ingredients,
        ])

        file_content = io.BytesIO(file_content.encode('utf-8'))

        return file_content

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

        return FileResponse(
            self._download_file(
                request=request,
                ingredients=ingredients
            ),
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

    filter_backends = (
        filters.SearchFilter,
    )
    filterset_class = IngredientFilter
    search_fields = ('=name',)

    pagination_class = None
