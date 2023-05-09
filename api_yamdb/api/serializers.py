from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

    class Meta:
        model = User
        fields = [
            "username",
            "confirmation_code",
        ]
        ordering = ["username"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "name",
            "slug",
        )
        model = Category


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("slug", "name")
        model = Genre
        lookup_field = "slug"


class TitlePostSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field="slug", queryset=Genre.objects.all(), many=True
    )

    class Meta:
        fields = ("id", "name", "description", "year", "category", "genre")
        model = Title


class TitleGetSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = (
            "id", "name", "rating", "year",
            "category", "genre", "description"
        )
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username")
    score = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = Review
        fields = ("id", "text", "score", "pub_date", "author")

    def validate(self, data):
        if self.context.get("request").method == "POST":
            author = self.context.get("request").user
            title_id = self.context.get("view").kwargs.get("title_id")
            if Review.objects.filter(author=author, title=title_id).exists():
                raise serializers.ValidationError(
                    "Вы уже оставляли отзыв на это произведение"
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username")

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date")


class AuthSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "username")

    def validate_username(self, name):
        if name == "me":
            raise serializers.ValidationError(
                'Имя пользователя "me" не разрешено.')
        return name

    def validate(self, data):
        username = data.get("username")
        email = data.get("email")
        if (
            User.objects.filter(username=username).exists()
            and User.objects.get(username=username).email != email
        ):
            raise serializers.ValidationError(
                "Пользователь с таким username уже зарегистрирован"
            )
        if (
            User.objects.filter(email=email).exists()
            and User.objects.get(email=email).username != username
        ):
            raise serializers.ValidationError(
                "Указанная почта уже зарегестрирована другим пользователем"
            )
        return data
