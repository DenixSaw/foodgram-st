from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from recipes.models import Recipe

USER_SELF_DATA_MAX_LENGTH = 150
USER_MAIL_MAX_LENGTH = 255
USER_NAME_REGEX_VALIDATOR = RegexValidator(regex=r'^[\w.@+-]+$')


# Модель пользователя системы на основе встроенной во фреймворке модели User
class User(AbstractUser):
    # Без этих строчек не работает авторизация. Просто абсурд
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        max_length=USER_SELF_DATA_MAX_LENGTH,
        unique=True,
        blank=False,
        validators=[USER_NAME_REGEX_VALIDATOR],
        verbose_name="Ник",
    )
    email = models.EmailField(
        max_length=USER_MAIL_MAX_LENGTH,
        unique=True,
        blank=False,
        verbose_name="Почта",
    )
    first_name = models.CharField(
        max_length=USER_SELF_DATA_MAX_LENGTH,
        blank=False,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=USER_SELF_DATA_MAX_LENGTH,
        blank=False,
        verbose_name="Фамилия",
    )
    avatar = models.ImageField(
        blank=True,
        verbose_name="Аватар",
        upload_to='avatars/',
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['username']

    def __str__(self):
        return self.username


# Модель подписки
class Follow(models.Model):
    # Кто подписан
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )

    # На кого подписан
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        unique_together = ('user', 'following')
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f'{self.user} подписан на {self.following}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_%(class)s"
            )
        ]
        ordering = ("-user",)

    def __str__(self):
        return f"{self.user} {self.recipe}"


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        default_related_name = "favorites"


class ShoppingCart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = "shopping_carts"
