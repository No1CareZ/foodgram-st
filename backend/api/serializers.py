from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer

from recipes.models import Ingredient, Recipe, \
    IngredientInRecipe


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """
    Serializer for User model inherited
    from UserSerializer for it simplicity.
    """

    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')

    class Meta():
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """
        Field creating function.
        """
        user = self.context.get('request').user

        return (
            user.is_authenticated
            and user.subscriber.filter(
                contentmaker=obj.pk
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """
    Serializer for requests to
    create avatar for user.
    """
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for Ingredient model.
    """

    read_only_fields = '__all__'

    class Meta():
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for Igredient model addtionaly has
    amount from IngredientInRecipe model and will
    be used in RecipeSerializer.
    """
    id = serializers.IntegerField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta():
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for Recipe model.
    """
    author = CustomUserSerializer()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredient'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        """
        Field creating function for
        is_favorited.
        """
        request = self.context.get('request')
        user = request.user

        return (
            user.is_authenticated
            and user.fav.filter(
                recipes=obj.pk
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Field creating function for
        is_in_shopping_cart.
        """
        request = self.context.get('request')
        user = request.user

        return (
            user.is_authenticated
            and request.user.buylist.filter(
                recipes=obj.pk
            ).exists()
        )


class CutRecipeSerializer(serializers.ModelSerializer):
    """
    Cutted serializer for Recipe model
    used for SubscriberSerializer. Mostly
    will be used in short actions like tests in
    Postman.
    """
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = fields


class SubscriberSerializer(CustomUserSerializer):
    """
    Serializer for subscriber-user pair.
    """
    recipes = serializers.SerializerMethodField(
        method_name='get_recipes'
    )
    recipes_count = serializers.IntegerField(
        source='recipe.count'
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
            'avatar',
            'is_subscribed'
        )

    def get_recipes(self, obj):
        """
        Getting recipes field.
        """
        queryset = obj.recipe.all()
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit:
            queryset = queryset[
                :int(recipes_limit)
            ]

        return CutRecipeSerializer(
            queryset,
            context={"request": request},
            many=True
        ).data

    def get_is_subscribed(self, obj):
        """
        Getting is_subscribed field.
        """
        user = self.context.get('request').user

        return (
            user.is_authenticated
            and user.subscriber.filter(
                contentmaker=obj.pk
            ).exists()
        )


class CreateIngredientSerializer(serializers.Serializer):
    """
    Serilizer for Ingredient creation.
    Will be used in other serilizers.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=1
    )

    class Meta():
        model = Ingredient
        fields = (
            "id",
            "amount"
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Serilizer for Recipe creation requests
    inherits from CreateIngredientSerializer
    to serialize ingredient.
    """
    ingredients = CreateIngredientSerializer(
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=1
    )

    class Meta():
        model = Recipe
        fields = (
            "name",
            "image",
            "text",
            "ingredients",
            "cooking_time",
        )

    def validate(self, data):
        """
        Ingredients validation.
        """
        ingredients = data.get("ingredients")

        if not ingredients:
            raise serializers.ValidationError(
                {
                    "ingredients": "Обязательное поле"
                }
            )

        ingredients_ids = [
            ingredient["ingredient"].id
            for ingredient in ingredients
        ]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {
                    "ingredients": "Ингредиенты не должны повторяться!"
                }
            )

        return data

    def validate_image(self, value):
        """
        Image validation.
        """
        if not value:
            raise serializers.ValidationError(
                {
                    "image": "Обязательное поле"
                }
            )

        return value

    def create(self, validated_data):
        """
        Owerwriting default create inoreder
        to work only with validated data.
        """
        ingredients = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """
        Owerwriting default update.
        """
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(validated_data.pop("ingredients"), instance)

        return super().update(instance, validated_data)

    def create_ingredients(self, ingredients, recipe):
        """
        Create ingredents.
        """
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                ingredient_id=ingredient["ingredient"].id,
                recipe=recipe,
                amount=ingredient["amount"]
            )
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context=self.context
        ).data
