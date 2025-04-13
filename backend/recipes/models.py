from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator, MinValueValidator


class CustomUser(AbstractUser):
    """
    Custom User model made from AbstructUser class.
    """
    email = models.EmailField(
        verbose_name='Почта',
        unique=True
    )
    username = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Никнейм должен проходить по правилам!'
            )
        ],
        unique=True,
        verbose_name='Никнейм'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        blank=True,
        upload_to='media/avatars/',
        verbose_name='Изображение профиля'
    )

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        related_query_name='customuser',
        blank=True,
        verbose_name='Группы',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        related_query_name='customuser',
        blank=True,
        verbose_name='Разрешения',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta():
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

    def __str__(self) -> str:
        return str(self.username)


class SubPair(models.Model):
    """
    Model of Subscribtion pair -
    subscriber a.k.a follower
    contentmaker a.k. followed.
    """
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    contentmaker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contentmaker'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'contentmaker'],
                name='Unique_SubPair'
            )
        ]
        verbose_name = 'Пара подписки'
        verbose_name_plural = 'Пары подписок'

    def __str__(self) -> str:
        return self.subscriber + ' подписан на ' + self.contentmaker


class Ingredient(models.Model):
    """
    Model of Ingredient.
    """
    name = models.CharField(
        max_length=128,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta():
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name + ' (' + self.measurement_unit + ')'


class Recipe(models.Model):
    """
    Model of Recipe.
    """
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    image = models.ImageField(
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Время готовки должно быть больше\
                     1 минуты. Никакого риса за 59 секунд!'
            )
        ],
        verbose_name='Время приготовления (мин.)'
    )

    author = models.ForeignKey(
        CustomUser,
        related_name='recipe',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipe',
        verbose_name='Автор рецепта'
    )
    posting_time = models.DateField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta():
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
    amount = models.SmallIntegerField(
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Количество едениц игридиента не может быть меньше 1!'
            )
        ],
    )

    class Meta():
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Unique_IngredientInRecipe'
            )
        ]

    def __str__(self) -> str:
        return self.ingredient + ' в ' + self.recipe + ' x' + self.amount


class AbstractUserRecipe(models.Model):
    """
    Abstract class needed to ensure abcense
    of repeating code for User and Recipe unique pair
    in other classes.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta():
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
        default_related_name = 'buylist'

    def __str__(self) -> str:
        return 'Список ' + self.user + 'для ' + self.recipes


class Favorite(AbstractUserRecipe):
    """
    Model of Favorite pair inherits from AbstractUserRecipe.
    """

    class Meta(AbstractUserRecipe.Meta):
        verbose_name = 'Пара избранное'
        verbose_name_plural = 'Пары избранное'
        default_related_name = 'fav'

    def __str__(self) -> str:
        return self.user + 'нравится ' + self.recipes
