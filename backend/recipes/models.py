from django.core.validators import MinValueValidator
from django.db import models

RECIPE_NAME_MAX_LENGTH = 256
INGREDIENT_NAME_MAX_LENGTH = 128
MEASUREMENT_UNIT_MAX_LENGTH = 64


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        blank=False,
        verbose_name="Название"
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        blank=False,
        verbose_name="Ед. измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        blank=False,
        verbose_name="Автор",
        related_name='recipes'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        blank=False,
        verbose_name="Название",
    )
    image = models.ImageField(
        blank=False,
        verbose_name="Изображение",
        upload_to="recipes/",
    )
    text = models.TextField(
        blank=False,
        verbose_name="Описание",
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        blank=False,
        verbose_name="Время приготовления",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        through_fields=('recipe', 'ingredient'),
        related_name='recipes'
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("id",)

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
        related_name='ingredients_in_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        validators=[MinValueValidator(1)],
        default=1,
        verbose_name="Количество",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        related_name='recipe_ingredients',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f"{self.ingredient.name}, {self.amount}"
