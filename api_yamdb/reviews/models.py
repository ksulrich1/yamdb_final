import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from .validators import year_validator

USER = "user"
MODERATOR = "moderator"
ADMIN = "admin"


class User(AbstractUser):
    ROLE_CHOICES = (
        (USER, "Пользователь"),
        (MODERATOR, "Модератор"),
        (ADMIN, "Администратор"),
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=150,
        unique=True,
        validators=[RegexValidator(regex=r"^[\w.@+-]",
                    message="Недопустимые символы")],
    )
    bio = models.TextField("Биография", blank=True)
    email = models.EmailField("Email", blank=False, unique=True)
    role = models.CharField(
        "Роль",
        max_length=9,
        choices=ROLE_CHOICES,
        default=USER,
    )
    confirmation_code = models.CharField(
        max_length=150, default=uuid.uuid4, editable=False
    )

    class Meta:
        ordering = ["-id"]

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    @property
    def is_admin(self):
        return self.role == ADMIN

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(verbose_name="Категория", max_length=256)
    slug = models.SlugField(
        verbose_name="Адрес категории",
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(regex=r"^[-a-zA-Z0-9_]+$",
                           message="Недопустимые символы")
        ],
    )

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.TextField(verbose_name="Жанр", max_length=256)
    slug = models.SlugField(
        verbose_name="Адрес жанра",
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(regex=r"^[-a-zA-Z0-9_]+$",
                           message="Недопустимые символы")
        ],
    )

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=256)
    year = models.IntegerField(validators=[year_validator])
    description = models.TextField(
        blank=True,
        null=True,
    )
    genre = models.ManyToManyField(
        Genre,
        related_name="title",
        verbose_name="Жанр",
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name="title"
    )

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Рассматриваемое произведение",
        help_text="Рассматриваемое произведение",
    )
    text = models.TextField(
        verbose_name="Текст рецензии",
        help_text="Оставьте свою рецензию",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецензии",
        help_text="Автор рецензии",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    score = models.IntegerField(
        verbose_name="Оценка",
        validators=(MinValueValidator(1), MaxValueValidator(10)),
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата рецензии",
        help_text="Дата рецензии",
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ("-pub_date", "score")
        constraints = [
            models.UniqueConstraint(fields=["title", "author"],
                                    name="unique review")
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        help_text="Произведение к которому относится коментарий",
        related_name="comments",
        verbose_name="Произведение",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
        help_text="Автор который оставил коментарий",
    )
    text = models.TextField(
        help_text="Текст нового коментария", verbose_name="Коментарий"
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Дата добавления нового коментария",
        verbose_name="Дата",
    )

    class Meta:
        ordering = ("pub_date",)

    def __str__(self):
        return self.text
