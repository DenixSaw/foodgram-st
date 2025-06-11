from rest_framework import routers
from django.urls import path, include

from .views import IngredientViewSet, UserCustomViewSet, RecipeViewSet, short_link_redirect

router = routers.DefaultRouter()
router.register(r'users', UserCustomViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<str:short_code>/',
         short_link_redirect,
         name='short-link-redirect'),
]
