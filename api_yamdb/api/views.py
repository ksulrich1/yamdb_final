from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title, User

from .filters import TitleFilter

from api_yamdb.settings import SITE_URL

from .permissions import (IsAdminUser, IsAdminUserOrReadOnly, IsModerator,
                          IsUserOrReadOnly)
from .serializers import (AuthSignUpSerializer, CategorySerializer,
                          CommentSerializer, GenreSerializer,
                          GetTokenSerializer, ReviewSerializer,
                          TitleGetSerializer, TitlePostSerializer,
                          UserSerializer)
from .utils import ListCreateDestroyViewSet


class CategoryViewSet(ListCreateDestroyViewSet):
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class TitleViewSet(viewsets.ModelViewSet):
    serializer_class = TitlePostSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filterset_class = TitleFilter
    filter_backends = (DjangoFilterBackend,)
    queryset = (
        Title.objects.all()
        .annotate(rating=Avg("reviews__score"))
        .order_by("-year", "name")
    )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TitleGetSerializer
        return TitlePostSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    search_fields = ("username",)
    filter_backends = (SearchFilter,)
    lookup_field = "username"
    http_method_names = ["get", "post", "delete", "patch"]

    @action(
        detail=False,
        methods=["GET", "PATCH"],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        if request.method == "GET":
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes((AllowAny,))
def signup(request):
    username = request.data.get("username")

    if not User.objects.filter(username=username).exists():
        serializer = AuthSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_confirmation_code(username)
        return Response(serializer.data, status=status.HTTP_200_OK)

    user = get_object_or_404(User, username=username)
    serializer = AuthSignUpSerializer(user, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    send_confirmation_code(username)
    return Response(serializer.data, status=status.HTTP_200_OK)


def send_confirmation_code(username):
    user = get_object_or_404(User, username=username)
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        "Код регистрации",
        f"Код для получения токена {confirmation_code}",
        SITE_URL,
        [user.email],
        fail_silently=False,
    )
    user.save()


@api_view(["POST"])
@permission_classes((AllowAny,))
def get_token(request):
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get("username")
    confirmation_code = serializer.validated_data.get("confirmation_code")
    user = get_object_or_404(User, username=username)
    if default_token_generator.check_token(
        user, str(confirmation_code)
    ):
        token_data = {"token": str(AccessToken.for_user(user))}
        return Response(token_data, status=status.HTTP_200_OK)
    return Response("Неверный код подтверждения",
                    status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsModerator | IsAdminUserOrReadOnly | IsUserOrReadOnly
    ]

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get("review_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get("review_id"))
        serializer.save(author=self.request.user, review=review)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsModerator | IsAdminUserOrReadOnly | IsUserOrReadOnly
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        serializer.save(author=self.request.user, title=title)
