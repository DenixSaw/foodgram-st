from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from backend.backend.settings import MEDIA_URL

USER_SELF_DATA_MAX_LENGTH = 150
USER_MAIL_MAX_LENGTH = 255


# Модель пользователя системы на основе встроенной во фреймворке модели User
class User(AbstractUser):
    username = models.CharField(
        max_length=USER_SELF_DATA_MAX_LENGTH,
        unique=True,
        blank=False,
        validators=[RegexValidator(regex='^[\w.@+-]+\z')],
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
    password = models.CharField(
        blank=False,
    )
    avatar = models.ImageField(
        blank=True,
        verbose_name="Аватар",
        upload_to=MEDIA_URL,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


# Модель подписки
class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        unique_together = ('user', 'following')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
