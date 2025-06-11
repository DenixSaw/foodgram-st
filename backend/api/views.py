from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .pagination import CommonPaginator
from .serializers import UserSerializer, IngredientSerializer, UserAvatarSerializer
from recipes.models import Ingredient, Recipe

# from users.models import User

User = get_user_model()


class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # pagination_class = CommonPaginator
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="me",
        url_name="me",
    )
    def me(self, request):
        serializer = UserSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=("put", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="avatar",
        url_name="avatar",
    )
    def avatar(self, request, id):
        if request.method == "PUT":
            return self.create_avatar(request)
        return self.delete_avatar(request)

    @staticmethod
    def create_avatar(self, request):
        serializer = UserAvatarSerializer(
            request.user, data=request.data, partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    search_fields = ("^name",)

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
