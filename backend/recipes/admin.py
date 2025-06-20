from django.contrib import admin
from .models import Ingredient, Recipe, IngredientRecipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


# Для возможности добавлять аля кортеж из ингредиента и количества
class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author',)
    inlines = (IngredientRecipeInline,)
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        return obj.favorites.count()

    favorites_count.short_description = 'В избранном у'

    fieldsets = (
        (None, {'fields': ('name', 'author', 'image', 'text', 'cooking_time')}),
        ('Дополнительно', {'fields': ('favorites_count',)}),
    )
