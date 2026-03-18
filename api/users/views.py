from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer, UserUpdateSerializer, \
    UserModel)
from .permissions import IsOwner


class UserRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user registration.

    Endpoints:
    - POST /api/auth/register/ - Create new user account
    """
    http_method_names =  ['post']

    serializer_class =  UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )

class UserLoginViewSet(viewsets.ModelViewSet):
    serializer_class =  UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        return Response(data, status=status.HTTP_200_OK)

class UserManagementViewSet(viewsets.GenericViewSet):

    serializer_class = UserUpdateSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        try:
            user = UserModel.objects.get(email=self.request.user.email)
        except UserModel.DoesNotExist:
            return UserModel.objects.none()

        return user

    @action(methods=['get', 'patch'], detail=False, url_path='me')
    def me(self, request, *args, **kwargs):

        if request.method == "PATCH":
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            updated_user = serializer.save()

            output_serializer = UserSerializer(updated_user)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = self.get_queryset()
            output_serializer = UserSerializer(queryset)

            return Response(output_serializer.data, status=status.HTTP_200_OK)






