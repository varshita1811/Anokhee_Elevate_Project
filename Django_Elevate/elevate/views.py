from django.shortcuts import render
from rest_framework.views import APIView
from .models import *
from rest_framework.response import Response 
from .serializers import *
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework import status

class manage_art_view(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        list_art=ARTTable.objects.all()
        json_art=art_serializers(list_art,many=True)

        return Response(json_art.data)
    
    def post(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "message": "Only Art Managers are allowed to create ARTs"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = art_serializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "ART created successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "message": "Only Art Managers are allowed to update ARTs"
                },
                status=status.HTTP_403_FORBIDDEN
            )
            
        art_id = request.query_params.get('art_id') or request.data.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required either in query params or body"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            art = ARTTable.objects.get(art_id=art_id)
        except ARTTable.DoesNotExist:
            return Response({"error": "ART not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = art_serializers(art, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "ART updated successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class manage_teams_view(APIView):
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if art_id:
            teams = TeamsTable.objects.filter(art=art_id)
        else:
            teams = TeamsTable.objects.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    def post(self, request):
    
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Team created successfully",
                    "data": serializer.data
                },
                status=201
            )
        return Response(serializer.errors, status=400)

    def put(self, request):
        team_id = request.query_params.get('team_id')
        if not team_id:
            return Response({"error": "team_id is required either in query params or body"}, status=400)
        try:
            team = TeamsTable.objects.get(team_id=team_id)
        except TeamsTable.DoesNotExist:
            return Response({"error": "Team not found"}, status=404)
        
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Team updated successfully",
                    "data": serializer.data
                },
                status=200
            )
        return Response(serializer.errors, status=400)

    def delete(self, request):
        team_id = request.query_params.get('team_id')
        art_id = request.query_params.get('art_id')
        
        if not team_id or not art_id:
            return Response({"error": "team_id and art_id are required in query parameters"}, status=400)
            
        try:
            team = TeamsTable.objects.get(team_id=team_id, art=art_id)
            team.delete()
            return Response({"message": "Team deleted successfully"}, status=200)
        except TeamsTable.DoesNotExist:
            return Response({"error": "Team not found with the provided team_id and art_id"}, status=404)


class manage_team_member_view(APIView):
    def get(self, request):
        team_id = request.query_params.get('team_id')
        user_id = request.query_params.get('user_id')
        
        team_members = TeamMembersTable.objects.all()
        if team_id:
            team_members = team_members.filter(team=team_id)
        if user_id:
            team_members = team_members.filter(user=user_id)
            
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Team member created successfully",
                    "data": serializer.data
                },
                status=201
            )
        return Response(serializer.errors, status=400)

    def put(self, request):
        team_id = request.query_params.get('team_id') or request.data.get('team_id')
        employee_id = request.query_params.get('employee_id') or request.data.get('employee_id')
        
        if not employee_id:
            # Maybe the user didn't pass employee_id, let's see if we can find by user_id and team_id instead if they passed user_id
            user_id = request.query_params.get('user_id') or request.data.get('user_id')
            if not user_id or not team_id:
               return Response({"error": "employee_id (or team_id and user_id) is required"}, status=400)
            try:
                team_member = TeamMembersTable.objects.get(team=team_id, user=user_id)
            except TeamMembersTable.DoesNotExist:
                return Response({"error": "Team member not found"}, status=404)
        else:
            try:
                if team_id:
                    team_member = TeamMembersTable.objects.get(employee_id=employee_id, team=team_id)
                else:
                     team_member = TeamMembersTable.objects.get(employee_id=employee_id)
            except TeamMembersTable.DoesNotExist:
                return Response({"error": "Team member not found"}, status=404)
        
        serializer = TeamMemberSerializer(team_member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Team member updated successfully",
                    "data": serializer.data
                },
                status=200
            )
        return Response(serializer.errors, status=400)

    def delete(self, request):
        team_id = request.query_params.get('team_id')
        employee_id = request.query_params.get('employee_id')
        
        if not team_id or not employee_id:
            return Response({"error": "team_id and employee_id are required in query parameters"}, status=400)
            
        try:
            team_member = TeamMembersTable.objects.get(employee_id=employee_id, team=team_id)
            team_member.delete()
            return Response({"message": "Team member deleted successfully"}, status=200)
        except TeamMembersTable.DoesNotExist:
            return Response({"error": "Team member not found with the provided employee_id and team_id"}, status=404)


class manage_sprint_view(APIView):
    def get(self, request):
        art_id = request.query_params.get('art_id')
        sprints = SprintTable.objects.all()
        if art_id:
            sprints = sprints.filter(art=art_id)
        serializer = SprintSerializer(sprints, many=True)
        return Response(serializer.data)

    def post(self, request):
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

    def put(self, request):
        sprint_id = request.query_params.get('sprint_id') or request.data.get('sprint_id')
        if not sprint_id:
            return Response({"error": "sprint_id is required either in query params or body"}, status=400)
            
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

    def delete(self, request):
        sprint_id = request.query_params.get('sprint_id')
        if not sprint_id:
            return Response({"error": "sprint_id is required in query parameters"}, status=400)
            
        try:
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
            sprint.delete()
            return Response({"message": "Sprint deleted successfully"}, status=200)
        except SprintTable.DoesNotExist:
            return Response({"error": "Sprint not found with the provided sprint_id"}, status=404)
