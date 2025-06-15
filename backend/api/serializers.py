from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from users.models import Follow, Favorite, ShoppingCart
from recipes.models import Ingredient, Recipe, IngredientRecipe

from api.fields import Binary64ImageField

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=user, following=obj
        ).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.avatar.url)
        return ''


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeFromFavouritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Binary64ImageField(use_url=True, required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredients', required=True)
    image = Binary64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate(self, data):
        ingredients = data.get("recipe_ingredients")

        if not ingredients:
            raise serializers.ValidationError(
                "Рецепт не может быть без ингредиентов"
            )

        ingredients_ids = [ingredient["id"] for ingredient in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не могут повторяться"
            )
        cooking_time = data.get("cooking_time")
        if not cooking_time:
            raise serializers.ValidationError(
                "Рецепт не может быть без времени приготовления"
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        IngredientRecipe.objects.filter(recipe=instance).delete()

        ingredients_data = validated_data.pop('recipe_ingredients', [])
        self.create_ingredients(ingredients_data, instance)

        return super().update(instance, validated_data)

    def create_ingredients(self, ingredients_data, recipe):
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                ingredient_id=ingredient_data['id'].id,  # Явно указываем ID ингредиента
                recipe=recipe,
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        ingredients = obj.recipe_ingredients.all()
        return [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount
            }
            for item in ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get("request")

        return (
                request is not None
                and request.user.is_authenticated
                and request.user.favorites.filter(pk=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")

        return (
                request is not None
                and request.user.is_authenticated
                and request.user.shopping_carts.filter(pk=obj.id).exists()
        )


class UserRecipeRelationSerializer(serializers.Serializer):
    class Meta:
        fields = ("user", "recipe")

    def to_representation(self, instance):
        serializer = RecipeFromFavouritesSerializer(
            instance.recipe,
            context=self.context
        )
        return serializer.data

    def validate(self, data, related_name):
        user = data.get("user")
        recipe = data.get("recipe")

        if getattr(user, related_name).filter(recipe__id=recipe.id).exists():
            raise serializers.ValidationError(
                f"{related_name} пользователя {user.username} "
                f"уже содержит рецепт {recipe.name}."
            )

        return data


class FavoriteSerializer(
    UserRecipeRelationSerializer, serializers.ModelSerializer
):
    class Meta(UserRecipeRelationSerializer.Meta):
        model = Favorite

    def validate(self, data):
        return super().validate(data, "favorites")


class ShoppingCartSerializer(
    UserRecipeRelationSerializer, serializers.ModelSerializer
):
    class Meta(UserRecipeRelationSerializer.Meta):
        model = ShoppingCart

    def validate(self, data):
        return super().validate(data, "shopping_carts")

class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.following.recipes.all()
        limit = request.query_params.get('recipes_limit')
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeFromFavouritesSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

    def get_avatar(self, obj):
        if obj.following.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.following.avatar.url)
        return None