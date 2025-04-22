from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """
    FilterSet for RecipeViewSet.
    """
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, _, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, _, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(to_buy_lists__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')


class IngredientFilter(filters.FilterSet):
    """
    FilterSet for IngredientViewSet.
    """
    class Meta:
        model = Ingredient
        fields = ('name',)
