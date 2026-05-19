from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render
from ..models import *
from ..serializers import *
from rest_framework import status
from django.db.models import Count
from ..utils import *

class SprintService:
    @staticmethod
    def get_sprints_for_art(request):
        try: 
            art_id = request.query_params.get('art_id')
            if art_id is None:
                return CommonService.error("art_id is required in query parameters",status_code=status.HTTP_400_BAD_REQUEST)            
            sprints = SprintTable.objects.filter(art__art_id=art_id)
            serializer = SprintSerializer(sprints, many=True)
            return CommonService.success(serializer.data)
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @staticmethod
    def create_sprint(request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to create sprints"
                },
                status=403
            )
        if not ARTTable.objects.filter(art_id=request.data.get('art')).exists() or ARTTable.objects.filter(art_id=request.data.get('art'), user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only create sprints for ARTs that you manage"
                },
                status=400
            )
        serializer = SprintSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Sprint created successfully",
                    "data": serializer.data
                },
                status=201
            )
        return Response(serializer.errors, status=400)
    
    @staticmethod
    def update_sprint(request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to update sprints"
                },
                status=403
            )
        if not ARTTable.objects.filter(art_id=request.data.get('art')).exists() or ARTTable.objects.filter(art_id=request.data.get('art'), user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only update sprints for ARTs that you manage"
                },
                status=400
            )
        sprint_id =  request.query_params.get('sprint_id')
        if not sprint_id:
            return Response({"error": "sprint_id is required in query parameters"}, status=400)
            
        try:
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
        except SprintTable.DoesNotExist:
            return Response({"error": "Sprint not found"}, status=404)
            
        serializer = SprintSerializer(sprint, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Sprint updated successfully",
                    "data": serializer.data
                },
                status=200
            )
        return Response(serializer.errors, status=400)
    
    @staticmethod
    def delete_sprint(request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to delete sprints"
                },
                status=403
            )
        if not ARTTable.objects.filter(art_id=request.query_params.get('art')).exists() or ARTTable.objects.filter(art_id=request.query_params.get('art'), user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only delete sprints for ARTs that you manage"
                },
                status=400
            ) 
        sprint_id = request.query_params.get('sprint_id')
        if not sprint_id:
            return Response({"error": "sprint_id is required in query parameters"}, status=400)
            
        try:
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
            sprint.delete()
            return Response({"message": "Sprint deleted successfully"}, status=200)
        except SprintTable.DoesNotExist:
            return Response({"error": "Sprint not found with the provided sprint_id"}, status=404)