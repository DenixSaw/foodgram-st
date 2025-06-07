from djoser.views import UserViewSet
from rest_framework import routers
from django.urls import path, include
from rest_framework.authtoken import views

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    #path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # path('auth/token/logout/', views.obtain_auth_token, name='logout')

]
