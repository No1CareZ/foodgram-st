from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import CustomUser, \
    SubPair, Ingredient, Recipe, \
    ToBuyList, Favorite


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Class to add CustomUser to admin.
    """
    list_display = (
        'pk',
        'email',
        'username',
        'first_name',
        'last_name',
        'avatar'
    )
    search_fields = (
        'email',
        'username'
    )


@admin.register(SubPair)
class SubPairAdmin(admin.ModelAdmin):
    """
    Class to add SubPair to admin.
    """
    list_display = (
        'pk',
        'subscriber',
        'contentmaker'
    )
    search_fields = (
        'subscriber__username',
        'contentmaker__username',
        'subscriber__email',
        'contentmaker__email'
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Class to add Ingredient to admin.
    """
    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Class to add Recipe to admin.
    """
    list_display = (
        'pk',
        'name',
        'image',
        'text',
        'cooking_time',
        'author',
        'get_ingredients',
        'get_fav'
    )
    search_fields = (
        'author__username',
        'name'
    )

    @admin.display(description="Ингридиенты")
    def get_ingredients(self, obj):
        """
        Return safe-string with information of amount, MU and
        name of the ingredient.
        """
        in_obj = obj.recipe_ingredient.all()
        safe_str = mark_safe(
            '<br>'.join(
                f'''{ing.ingredient.name} \
                ({ing.ingredient.measurement_unit}) \
                — {ing.ingredient.amount}'''
                for ing in in_obj
            )
        )

        return safe_str

    @admin.display(description="В избранном у")
    def get_fav(self, obj):
        """
        Get count of haow may times
        this recpie was add into Favorite.
        """
        return obj.fav.count()


@admin.register(ToBuyList)
class ToBuyListAdmin(admin.ModelAdmin):
    """
    Class to add ToBuyList to admin.
    """
    list_display = (
        'pk',
        'user',
        'recipes'
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Class to add Favorite to admin.
    """
    list_display = (
        'pk',
        'user',
        'recipes'
    )
