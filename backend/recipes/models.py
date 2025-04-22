from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

import constant


class User(AbstractUser):
    """
    User model made from AbstructUser class.
    """

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        verbose_name='Почта',
        unique=True
    )
    username = models.CharField(
        max_length=constant.USERNAME_MAX_LENGTH,
        validators=[
            RegexValidator(
                regex=constant.USERNAME_VALIDATOR_REGEX,
                message='Username must follow the rules!'
            )
        ],
        unique=True,
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=constant.FNAME_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=constant.LNAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        blank=True,
        upload_to='media/avatars/',
        verbose_name='Изображение профиля'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

    def __str__(self) -> str:
        return str(self.username)


class SubPair(models.Model):
    """
    Model of Subscribtion pair -
    subscriber a.k.a follower
    content_maker a.k. followed.
    """

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    content_maker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='content_maker'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'content_maker'],
                name='Unique_SubPair'
            )
        ]
        verbose_name = 'Пара подписки'
        verbose_name_plural = 'Пары подписок'

    def __str__(self) -> str:
        return f'{self.subscriber} подписан на {self.content_maker}'


class Ingredient(models.Model):
    """
    Model of Ingredient.
    """

    name = models.CharField(
        max_length=constant.INGREDIENT_MAX_NAME,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=constant.INGREDIENT_MAX_MU,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """
    Model of Recipe.
    """

    name = models.CharField(
        max_length=constant.RECIPE_MAX_NAME,
        verbose_name='Название'
    )
    image = models.ImageField(
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                limit_value=constant.RECIPE_COOKING_TIME_LIMIT_VALUE,
                message=f'''Cooking time must be greater than {
                    constant.RECIPE_COOKING_TIME_LIMIT_VALUE
                } minutes.'''
            )
        ],
        verbose_name='Время приготовления (мин.)'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Автор рецепта'
    )
    posting_time = models.DateField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-posting_time',)

    def __str__(self) -> str:
        return str(self.name)


class IngredientInRecipe(models.Model):
    """
    Model for storing 'amount' value of Ingredient object In Recipe object.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                limit_value=constant.ING_IN_REC_AMOUNT_LIMIT_VALUE,
                message=f'''The quantity of ingredient cannot be less than {
                    constant.ING_IN_REC_AMOUNT_LIMIT_VALUE
                }!'''
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Unique_IngredientInRecipe'
            )
        ]

    def __str__(self) -> str:
        return f'{self.ingredient} в {self.recipe} x{self.amount}'


class AbstractUserRecipe(models.Model):
    """
    Abstract class needed to ensure abcense
    of repeating code for User and Recipe unique pair
    in other classes.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='Unique_%(class)s'
            )
        ]


class ToBuyList(AbstractUserRecipe):
    """
    Model of ToBuyList inherits from AbstractUserRecipe.
    """

    class Meta(AbstractUserRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'to_buy_lists'

    def __str__(self) -> str:
        return f'Список {self.user} для {self.recipes}'


class Favorite(AbstractUserRecipe):
    """
    Model of Favorite pair inherits from AbstractUserRecipe.
    """

    class Meta(AbstractUserRecipe.Meta):
        verbose_name = 'Пара избранное'
        verbose_name_plural = 'Пары избранное'
        default_related_name = 'favorites'

    def __str__(self) -> str:
        return f'{self.user} нравится {self.recipes}'
