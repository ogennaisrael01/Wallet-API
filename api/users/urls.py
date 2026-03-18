from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import UserRegistrationViewSet, UserLoginViewSet, UserManagementViewSet

router = DefaultRouter()

router.register("register", UserRegistrationViewSet, basename="register")
router.register("login", UserLoginViewSet, basename="login")
router.register("profile", UserManagementViewSet, basename='profile')

urlpatterns = [
    path("auth/", include(router.urls))
]