from djoser.views import UserViewSet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer, IngredientSerializer
from recipes.models import Ingredient, Recipe


class UserCustomViewSet(UserViewSet):
    serializer_class = UserSerializer


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
