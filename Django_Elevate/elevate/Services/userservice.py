from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render
from ..models import *
from ..serializers import *
from rest_framework import status
from django.db.models import Count
from ..utils import *


class UserService:

    ##TODO
    ##implement new API to get all users, dont show confidential info like password, and also implement pagination for it
    @staticmethod
    def get_user_details(request):
        try: 
            users = User.objects.filter(user_id=request.user.user_id)
            serializer = UserSerializer(users, many=True)
            for user_data in serializer.data:
                user_data.pop('password', None)
            return CommonService.success(serializer.data)
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @staticmethod
    def update_user_details(request):
        user_id = request.user.user_id
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return CommonService.error("User not found",status_code=status.HTTP_404_NOT_FOUND)
            
        user_login = request.data.get('user_login', user.user_login)
        user_firstname = request.data.get('user_firstname', user.user_firstname)
        user_lastname = request.data.get('user_lastname', user.user_lastname)
        password = request.data.get('password')
        user_role = request.data.get('user_role', user.user_role)
        image = request.FILES.get("image") or request.FILES.get("user_image")

        user = User.objects.filter(user_id=user_id).first()
        user.user_login = user_login
        user.user_firstname = user_firstname
        user.user_lastname = user_lastname
        if user_role in ["Admin", "Art Manager"]:
            user.user_role = user_role
            user.is_active = False
        else:
            user.user_role = user_role
        if image:
            ext = image.name.split('.')[-1]
            file_name = f"user_{user.user_id}_{uuid.uuid4()}.{ext}"
            image.name = file_name
            user.user_image = image
        if password:
            user.set_password(password)
        user.save()
        return CommonService.success(user.user_id,"User updated successfully")
    
    @staticmethod
    def delete_user(request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return CommonService.error("user_id is required in query parameters",status_code=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(user_id=user_id)
            user.delete()
            return CommonService.success("User deleted successfully",status_code=status.HTTP_200_OK)
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
