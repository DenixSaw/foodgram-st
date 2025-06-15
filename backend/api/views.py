import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import serializers
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import UserSerializer, IngredientSerializer, UserAvatarSerializer, ShoppingCartSerializer, \
    FavoriteSerializer, CreateRecipeSerializer, RecipeSerializer, RecipeFromFavouritesSerializer, FollowSerializer
from recipes.models import Ingredient, Recipe, IngredientRecipe
from users.models import Follow, ShoppingCart, Favorite

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

    def create_avatar(self, request):
        if not request.data or 'avatar' not in request.data:
            return Response(
                {"avatar": ["Это поле обязательно."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserAvatarSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        following = self.get_object()

        if request.method == 'POST':
            if user == following:
                return Response(
                    {"detail": "Нельзя подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Follow.objects.create(user=user, following=following)
            serializer = FollowSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Follow.objects.filter(
                user=user,
                following=following
            ).first()

            if not subscription:
                return Response(
                    {"detail": "Подписка не найдена"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user).select_related('following')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = FollowSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = FollowSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    search_fields = ("^name",)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return CreateRecipeSerializer

        return RecipeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_favorited = self.request.query_params.get('is_favorited')

        if is_favorited in ("1", 1, True) and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=self.request.user)

        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart in ("1", 1, True) and self.request.user.is_authenticated:
            queryset = queryset.filter(shopping_carts__user=self.request.user)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="favorite",
        url_name="favorite",
    )
    def favorite(self, request, pk):
        if request.method == "POST":
            return self.add_recipe_to_favorite(
                request, pk
            )
        return self.delete_user_recipe_relation(
            request,
            pk,
            "favorites",
            Favorite.DoesNotExist,
            "Рецепт не в избранном.",
        )

    def add_recipe_to_favorite(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Рецепт не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user.favorites.filter(recipe_id=pk).exists():
            return Response(
                {"errors": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(user=request.user, recipe=recipe)

        serializer = RecipeFromFavouritesSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_user_recipe_relation(
            self,
            request,
            pk,
            related_name_for_user,
            does_not_exist_exception,
            does_not_exist_message,
    ):
        if not Recipe.objects.filter(id=pk).exists():  # Если рецепта нет в БД
            return Response(
                {"error": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            getattr(request.user, related_name_for_user).get(
                user=request.user, recipe_id=pk
            ).delete()
        except does_not_exist_exception:
            return Response(
                does_not_exist_message,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.add_recipe_to_cart(
                request, pk
            )
        return self.delete_user_recipe_relation(
            request,
            pk,
            "shopping_carts",
            ShoppingCart.DoesNotExist,
            "Рецепт не в корзине",
        )

    def add_recipe_to_cart(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Рецепт не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.user.shopping_carts.filter(recipe_id=pk).exists():
            return Response(
                {"errors": "Рецепт уже в корзине."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ShoppingCart.objects.create(user=request.user, recipe=recipe)

        serializer = RecipeFromFavouritesSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        get_object_or_404(Recipe, id=pk)
        short_link = f"localhost/s/{pk}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_cart(self, request):
        ingredient_data = self.get_ingredients(request.user)
        return self.make_file(ingredient_data)

    def get_ingredients(self, user):
        return (
            IngredientRecipe.objects
            .filter(recipe__shopping_carts__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(quantity=Sum('amount'))
            .order_by('ingredient__name')
        )

    def make_file(self, ingredient_records):
        file_lines = [
            f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}) - {item['quantity']}"
            for item in ingredient_records
        ]

        with tempfile.NamedTemporaryFile(
                mode='w+',
                suffix='.txt',
                encoding='UTF-8',
                delete=False
        ) as tmp:
            tmp.write('\n'.join(file_lines))
            tmp.flush()

            response = FileResponse(
                open(tmp.name, 'rb'),
                as_attachment=True,
                filename='cart.txt',
                content_type='text/plain'
            )

            return response


def short_link_redirect(request, short_code):
    recipe = get_object_or_404(Recipe, id=short_code)
    return redirect(f'/recipes/{recipe.id}/')
