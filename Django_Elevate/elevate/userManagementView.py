import uuid
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from elevate.models import User
from django.db import IntegrityError
import re


class SignupView(APIView):

    def post(self, request):
        user_login = request.data.get("user_login")
        user_firstname = request.data.get("user_firstname")
        user_lastname = request.data.get("user_lastname")
        password = request.data.get("password")
        user_role = request.data.get("user_role")
        user_image = request.data.get("user_image", None)

        if not user_login or not password:
            return Response(
                {"error": "user login and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Regex to check for special characters
        # Allows alphanumeric characters (a-z, A-Z, 0-9) and spaces, but limits user_login to no spaces
        if not re.match(r'^[a-zA-Z0-9]+$', user_login):
            return Response(
                {"error": "user_login cannot contain special characters or spaces"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user_firstname and not re.match(r'^[a-zA-Z0-9 ]+$', user_firstname):
            return Response(
                {"error": "user_firstname cannot contain special characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user_lastname and not re.match(r'^[a-zA-Z0-9 ]+$', user_lastname):
            return Response(
                {"error": "user_lastname cannot contain special characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(user_login=user_login).exists():
            return Response(
                {"error": "User with this login already exists, Please choose a different login name"},
                status=status.HTTP_409_CONFLICT
            )

        try:
            user = User.objects.create_user(
                user_login=user_login,
                user_firstname=user_firstname,
                user_lastname=user_lastname,
                password=password,
                user_role=user_role,
            )

            image = request.FILES.get("image") or request.FILES.get("user_image")
            if image:
                ext = image.name.split('.')[-1]
                file_name = f"user_{user.user_id}_{uuid.uuid4()}.{ext}"
                image.name = file_name
                user.user_image = image
                user.save()
            else:
                print("No image uploaded")
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {"error": "User already exists, Please choose a different login name"},
                status=status.HTTP_409_CONFLICT
            )
    


class LoginView(APIView):

    def post(self, request):
        user_login = request.data.get("user_login")
        password = request.data.get("password")
        request_user_role = request.data.get("user_role") or "Employee"

        user = authenticate(
            request,
            user_login=user_login,
            password=password
        )

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if (request_user_role == "Employee" and user.user_role in ["Admin", "Art Manager"]) or (request_user_role in ["Admin", "Art Manager"] and user.user_role != request_user_role):
            return Response(
                {"error": "User role mismatch"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "user_id": user.user_id,
                "user_login": user.user_login,
                "user_role": user.user_role,
            }
        })
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_205_RESET_CONTENT
        )