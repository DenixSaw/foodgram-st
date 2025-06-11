from djoser.views import UserViewSet
from rest_framework import routers
from django.urls import path, include

from .views import IngredientViewSet, UserCustomViewSet

router = routers.DefaultRouter()
router.register(r'users', UserCustomViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
