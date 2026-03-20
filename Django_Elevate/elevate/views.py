from django.utils import timezone
from datetime import timedelta

from .services import *
from django.shortcuts import render
from rest_framework.views import APIView
from .models import *
from rest_framework.response import Response 
from .serializers import *
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework import status
from django.db.models import Count

class manage_art_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        list_art=ARTTable.objects.filter(user__user_id=request.user.user_id)
        if not list_art.exists():
            return Response({"error": "No ARTs found for this user"}, status=status.HTTP_404_NOT_FOUND)
        json_art=art_serializers(list_art,many=True)
        ##add user name and image in response
        for art in json_art.data:
            user = User.objects.get(user_id=art['user'])
            art['art_manager_name'] = f"{user.user_firstname} {user.user_lastname}"
            art['art_manager_image'] = user.user_image.url if user.user_image else "" 

        return Response(json_art.data)
    
    def post(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to create ARTs"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        if str(request.data.get('user')) != str(request.user.user_id):
            return Response(
                {
                    "error": "You can only create ARTs for yourself. The user field must match your user_id."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        if ARTTable.objects.filter(art_name=request.data.get('art_name')).exists():
            return Response(
                {
                    "error": "An ART with this name already exists. Please choose a different name."
                },
                status=status.HTTP_400_BAD_REQUEST
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
                    "error": "Only Art Managers are allowed to update ARTs"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        art_id = request.query_params.get('art_id') or request.data.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required either in query params or body"}, status=status.HTTP_400_BAD_REQUEST)
        if not ARTTable.objects.filter(art_id=art_id, user__user_id=request.user.user_id).exists():
            return Response({"error": "ART not found or you do not have permission to update this ART"}, status=status.HTTP_404_NOT_FOUND)
        try:
            art = ARTTable.objects.get(art_id=art_id, user__user_id=request.user.user_id)
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
    def delete(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to delete ARTs"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        if not ARTTable.objects.filter(art_id=art_id, user__user_id=request.user.user_id).exists():
            return Response({"error": "ART not found or you do not have permission to delete this ART"}, status=status.HTTP_404_NOT_FOUND)
        try:
            art = ARTTable.objects.get(art_id=art_id, user__user_id=request.user.user_id)
            art.delete()
            return Response({"message": "ART deleted successfully"}, status=status.HTTP_200_OK)
        except ARTTable.DoesNotExist:
            return Response({"error": "ART not found with the provided art_id"}, status=status.HTTP_404_NOT_FOUND)

class manage_teams_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        teams = TeamsTable.objects.filter(art=art_id)
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to create teams"
                },
                status=403
            )
        if not ARTTable.objects.filter(art_id=request.data.get('art')).exists() or ARTTable.objects.filter(art_id=request.data.get('art'), user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only create teams for ARTs that you manage"
                },
                status=400
            )

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
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to update teams"
                },
                status=403
            )
        if not ARTTable.objects.filter(art_id=request.data.get('art')).exists() or ARTTable.objects.filter(art_id=request.data.get('art'), user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only update teams for ARTs that you manage"
                },
                status=400
            )
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
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers are allowed to delete teams"
                },
                status=403
            )
        art = ARTTable.objects.filter(user__user_id=request.user.user_id).first()
        if not art or not ARTTable.objects.filter(art_id=art.art_id, user__user_id=request.user.user_id).exists():
            return Response(
                {
                    "error": "The art field must reference a valid ART and you can only delete teams for ARTs that you manage"
                },
                status=400
            )
        team_id = request.query_params.get('team_id')
        art_id = art.art_id if art else None
        if not team_id or not art_id:
            return Response({"error": "team_id and art_id are required in query parameters"}, status=400)
            
        try:
            team = TeamsTable.objects.get(team_id=team_id, art=art_id)
            team.delete()
            return Response({"message": "Team deleted successfully"}, status=200)
        except TeamsTable.DoesNotExist:
            return Response({"error": "Team not found with the provided team_id and art_id"}, status=404)


class manage_team_member_view(APIView):
    permission_classes = [IsAuthenticated]

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
        if request.user.user_role == "Art Manager" or request.user.user_role == "Admin":
            return Response(
                {
                    "error": "Art Managers and Admins cannot join as team members. Only Employees can join teams as members."
                },
                status=400
            )
        if TeamsTable.objects.filter(team_id=request.data.get('team')).first() is None:
            return Response(
                {
                    "error": "The team field must reference a valid team that exists"
                },
                status=400
            )
        serializer = TeamMemberSerializer(data=request.data)
        if serializer.is_valid():
            TeamMembersTable.objects.create(
                team_id=serializer.validated_data['team'].team_id,
                user_id=request.user.user_id,
                is_active=False
            )
            return Response(
                {
                    "message": "Team member created successfully",
                },
                status=201
            )
        return Response(serializer.errors, status=400)

    def put(self, request):
        team_id = request.data.get('team_id')
        is_active = request.data.get('is_active')
        employee_id = request.query_params.get('employee_id')
        print(team_id,is_active,employee_id,request.user.user_id)
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers can update team member status"
                },
                status=403
            )
        if is_active is None or team_id is None or employee_id is None:
            return Response(
                {
                    "error": "is_active, team_id, and employee_id are required to update team member status"
                },
                status=400
            )
        if not TeamsTable.objects.filter(team_id=team_id).exists() or TeamMembersTable.objects.filter(employee_id=employee_id, team__team_id=team_id, team__art__user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The team_id provided does not reference a valid team"
                },
                status=400
             )

        team = TeamMembersTable.objects.filter(employee_id=employee_id, team__team_id=team_id).first()
        team.is_active = is_active
        team.team_id = team_id
        team.save()
        return Response(
            {
                "message": "Team member status updated successfully"
            },
            status=200
        )


    def delete(self, request):
        if request.user.user_role != "Art Manager":
            return Response(
                {
                    "error": "Only Art Managers can delete team members"
                },
                status=403
                )
        if not TeamsTable.objects.filter(team_id=request.data.get('team_id')).exists() or TeamMembersTable.objects.filter(employee_id=request.query_params.get('employee_id'), team__team_id=request.query_params.get('team_id'), team__art__user__user_id=request.user.user_id).first() is None:
            return Response(
                {
                    "error": "The team_id provided does not reference a valid team or you do not have permission to delete members from this team"
                }
                ,status=400
                )
        employee_id = request.query_params.get('employee_id')
        team_id = request.data.get('team_id')
        try:
            team_member = TeamMembersTable.objects.get(employee_id=employee_id, team__team_id=team_id)
            team_member.delete()
            return Response({"message": "Team member deleted successfully"}, status=200)
        except TeamMembersTable.DoesNotExist:
            return Response({"error": "Team member not found with the provided employee_id and team_id"}, status=404)


class manage_sprint_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if art_id is None:
            return Response({"error": "art_id is required in query parameters"}, status=400)
        
        sprints = SprintTable.objects.filter(art__art_id=art_id)
        serializer = SprintSerializer(sprints, many=True)
        return Response(serializer.data)

    def post(self, request):
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

    def put(self, request):
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

    def delete(self, request):
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

class manage_user_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):        
        users = User.objects.filter(user_id=request.user.user_id)
        
        serializer = UserSerializer(users, many=True)
        for user_data in serializer.data:
            user_data.pop('password', None)
        return Response(serializer.data)

    def put(self, request):
        ##TODO needs lots of checks to ensure only admins can update roles and only art managers can update users in their ARTs etc
        user_id = request.query_params.get('user_id') or request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required either in query params or body"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
         
            if 'password' in request.data:
                user.set_password(request.data['password'])
            
            serializer.save()
            return Response(
                {
                    "message": "User updated successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(user_id=user_id)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found with the provided user_id"}, status=status.HTTP_404_NOT_FOUND)

class get_nomination_data_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_id = request.user.user_id
        teammember = TeamMembersTable.objects.filter(user__user_id=user_id).first()
        team_art = teammember.team.art if teammember else None
        
        sprint_id = SprintTable.objects.filter(art=team_art,status='Active').values_list('sprint_id', flat=True).first()
        if sprint_id is None:
            return Response({"error": "No active sprint found for the user's ART"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
            sprint_name = sprint.sprint_name

            employee_id = TeamMembersTable.objects.filter(user__user_id=user_id).values_list('employee_id', flat=True).first()
            
           
            nominations = NominationsTable.objects.filter(nominator__employee_id=employee_id, sprint=sprint_id)
            awards_used = []
            for nom in nominations:
                awards_used.append({
                    "award_id": str(nom.award.award_id),
                    "award_name": nom.award.award_name,
                    "award_description": nom.award.award_description
                })
                
            # Find User's Team
            try:
                user_team_member = TeamMembersTable.objects.get(user__user_id=user_id)
                user_team = user_team_member.team
                art = user_team.art
                
                # 3. User Team Members
                # Exclude the user themselves from their team list
                user_team_members_qs = TeamMembersTable.objects.filter(team=user_team).exclude(user__user_id=user_id)
                user_team_members = []
                for member in user_team_members_qs:
                    user_team_members.append({
                        "employee_id": str(member.employee_id),
                        "employee_name": f"{member.user.user_firstname} {member.user.user_lastname}",
                        "team_name": user_team.team_name,
                        "employee_role": member.user.user_role,
                        "employee_image": member.user.user_image.url if member.user.user_image else ""
                    })
                    
                # 4. Other Team Members
                other_teams = TeamsTable.objects.filter(art=art).exclude(team_id=user_team.team_id)
                other_team_members_qs = TeamMembersTable.objects.filter(team__in=other_teams)
                other_team_members = []
                for member in other_team_members_qs:
                    other_team_members.append({
                        "employee_id": str(member.employee_id),
                        "employee_name": f"{member.user.user_firstname} {member.user.user_lastname}",
                        "team_name": member.team.team_name,
                        "employee_role": member.user.user_role,
                        "employee_image": member.user.user_image.url if member.user.user_image else ""
                    })
            except TeamMembersTable.DoesNotExist:
                user_team_members = []
                other_team_members = []
                
            return Response({
                "sprint_name": sprint_name,
                "awards_already_used": awards_used,
                "user_team_members": user_team_members,
                "other_team_members": other_team_members
            }, status=status.HTTP_200_OK)
            
        except SprintTable.DoesNotExist:
            return Response({"error": "Sprint not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class create_nomination_view(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        nominator_id = request.data.get('nominator_id').replace("-","") if request.data.get('nominator_id') else None
        nominee_id = request.data.get('nominee_id').replace("-","") if request.data.get('nominee_id') else None
        sprint_id = request.data.get('sprint_id').replace("-","") if request.data.get('sprint_id') else None
        award_id = request.data.get('award_id') if request.data.get('award_id') else None
        comments = request.data.get('comments')
        if not all([nominator_id, nominee_id, award_id, comments]):
            return Response({"error": "nominator_id, nominee_id, award_id, and comments are required"}, status=status.HTTP_400_BAD_REQUEST)

        if TeamMembersTable.objects.filter(user__user_id=request.user.user_id,employee_id=nominator_id).exists() is False:
            return Response({"error": "You can only nominate if using your creds."}, status=status.HTTP_403_FORBIDDEN)
        


        try:
            # 1. Validate Nominator
            nominator = TeamMembersTable.objects.filter(employee_id=nominator_id).first()
            print("Nominator:", nominator)
            # 2. Validate Nominated Employee
            nominee = TeamMembersTable.objects.filter(employee_id=nominee_id).first()
            print("Nominee:", nominee)
            nominee_user = nominee.user
            
            # 3. Validate Award
            award = AwardsTable.objects.get(award_id=award_id)
            
            # 4. Get or infer Sprint
            if sprint_id:
                sprint = SprintTable.objects.get(sprint_id=sprint_id)
            else:
                sprint = SprintTable.objects.filter(art=nominee.team.art).order_by('-created_at').first()
                if not sprint:
                    return Response({"error": "No sprint found. Please provide sprint_id."}, status=status.HTTP_400_BAD_REQUEST)
            print("Sprint:", sprint)
            print("Nominee Employee ID:", nominee.employee_id)
            print("Nominator Employee ID:", nominator.employee_id) 
            # 5. Check nominations left
            nominations_made = NominationsTable.objects.filter(nominator=nominator, sprint=sprint, nominee=nominee).count()
            print("Nominations Made:", nominations_made)
            nominations_left = 5 - nominations_made
            if nominations_left <= 0:
                return Response({"error": "You have exhausted your 5 nominations for this sprint."}, status=status.HTTP_400_BAD_REQUEST)
                
            # 6. Create Nomination
            nomination = NominationsTable.objects.create(
                nominee=nominee,
                nominator=nominator,
                award=award,
                sprint=sprint,
                comments=comments,
            )
            
            # 7. Update User table
            points_to_add = 10 
            nominee_user.no_of_awards = (nominee_user.no_of_awards or 0) + 1
            nominee_user.no_of_points = (nominee_user.no_of_points or 0) + points_to_add
            nominee_user.save()
            
            # 8. Update JiraTasksTable
            jira_task = JiraTasksTable.objects.filter(employee=nominee, sprint=sprint).first()
            if jira_task:
                jira_task.no_of_awards = (jira_task.no_of_awards or 0) + 1
                jira_task.no_of_points = (jira_task.no_of_points or 0) + points_to_add
                jira_task.save()
            else:
                JiraTasksTable.objects.create(
                    employee=nominee,
                    sprint=sprint,
                    team=nominee.team,
                    no_of_awards=1,
                    no_of_points=points_to_add,
                    tasks = None 
                )
                
            return Response({
                "message": "Nomination created successfully",
                "data": {
                    "nomination_id": str(nomination.nomination_id),
                    "no_of_nominations_left": nominations_left-1
                }
            }, status=status.HTTP_201_CREATED)
            
        except TeamMembersTable.DoesNotExist:
            return Response({"error": "Nominator not found"}, status=status.HTTP_404_NOT_FOUND)
        except TeamMembersTable.DoesNotExist:
            return Response({"error": "Nominated employee not found"}, status=status.HTTP_404_NOT_FOUND)
        except AwardsTable.DoesNotExist:
            return Response({"error": "Award not found"}, status=status.HTTP_404_NOT_FOUND)
        except SprintTable.DoesNotExist:
            return Response({"error": "Sprint not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class get_current_sprint_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        team = TeamMembersTable.objects.filter(user__user_id=request.user.user_id).select_related('team').first()
        art_id = TeamsTable.objects.filter(team_id=team.team_id).values_list('art_id', flat=True).first() if team else None
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_sprint = SprintTable.objects.filter(art=art_id, status="Active").first()
            if not current_sprint:
                return Response({"error": "No active sprint found for this ART"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = SprintSerializer(current_sprint)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class get_leaderboard_art_level_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id or ARTTable.objects.filter(art_id=art_id).first() is None:
            return Response({"error": "art_id is invalid or not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        get_current_sprint_view_instance = get_current_sprint_view()
        sprint_response = get_current_sprint_view_instance.get(request)
        if sprint_response.status_code != 200: 
            return Response({"error": "Could not fetch current sprint information"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sprint_id = sprint_response.data.get("sprint_id")
        if not sprint_id:
            return Response({"error": "No active sprint found for the user's ART"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all team members in this ART
        team_members = TeamMembersTable.objects.filter(team__art__art_id=art_id).select_related('user') 
        
        leaderboard = []
        for member in team_members:
            user = member.user
            # Fetch all nominations for this employee
            nominations = NominationsTable.objects.filter(nominee=member, sprint_id=sprint_id).select_related('award')
            # Group nominations by award  
            awards_dict = {}
            for nom in nominations:
                award_id_str = str(nom.award.award_id)
                if award_id_str not in awards_dict:
                    awards_dict[award_id_str] = {
                        "award_name": nom.award.award_name,
                        "award_image": nom.award.award_image.url if nom.award.award_image else "",
                        "total_nomniations_for_award": 0,
                        "nominations_information": []
                    }
                
                awards_dict[award_id_str]["total_nomniations_for_award"] += 1
                # Fetch nominator details
                try:
                    nominator_user = User.objects.get(user_id=nom.nominator.user.user_id) if nom.nominator and nom.nominator.user else None 
                    nominator_name = f"{nominator_user.user_firstname} {nominator_user.user_lastname}".strip()
                except User.DoesNotExist:
                    nominator_name = "Unknown"
                awards_dict[award_id_str]["nominations_information"].append({
                    "nominator": nominator_name,
                    "nomination_date": nom.nomination_date.strftime("%Y-%m-%d") if nom.nomination_date else nom.created_at.strftime("%Y-%m-%d"),
                    "comments": nom.comments
                })
            
            list_of_awards = list(awards_dict.values())
            # Add to leaderboard if they have points or awards
            if (user.no_of_points and user.no_of_points > 0) or list_of_awards:
                leaderboard.append({
                    "employeename": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "image": user.user_image.url if user and user.user_image else "",
                    "total_awards": user.no_of_awards or 0,
                    "total_no_of_points": user.no_of_points or 0,
                    "List_of_awards": list_of_awards
                })
        # Sort leaderboard by total_no_of_points in descending order
        leaderboard.sort(key=lambda x: x["total_no_of_points"], reverse=True)
        return Response(leaderboard, status=status.HTTP_200_OK)

class get_leaderboard_team_level_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        team_id = TeamMembersTable.objects.filter(user__user_id=request.user.user_id).values_list('team__team_id', flat=True).first()
        if not team_id or team_id is None:
            return Response({"error": "team_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        get_current_sprint_view_instance = get_current_sprint_view()
        sprint_response = get_current_sprint_view_instance.get(request)
        if sprint_response.status_code != 200: 
            return Response({"error": "Could not fetch current sprint information"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sprint_id = sprint_response.data.get("sprint_id")
        if not sprint_id:
            return Response({"error": "No active sprint found for the user's ART"}, status=status.HTTP_400_BAD_REQUEST)


        # Get all team members in this specific team
        team_members = TeamMembersTable.objects.filter(team=team_id).select_related('user')
        
        leaderboard = []
        for member in team_members:
            user = member.user
            
            # Fetch all nominations for this employee
            nominations = NominationsTable.objects.filter(nominee__employee_id=member.employee_id, sprint=sprint_id).select_related('award')
            
            # Group nominations by award
            awards_dict = {}
            for nom in nominations:
                award_id_str = str(nom.award.award_id)
                if award_id_str not in awards_dict:
                    awards_dict[award_id_str] = {
                        "award_name": nom.award.award_name,
                        "award_image": nom.award.award_image.url if nom.award and nom.award.award_image else "",
                        "total_nominations_for_award": 0,
                        "nominations_information": []
                    }
                
                awards_dict[award_id_str]["total_nominations_for_award"] += 1
                
                # Fetch nominator details
                try:
                    nominator_user = User.objects.get(user_id=nom.nominator.user.user_id)
                    nominator_name = f"{nominator_user.user_firstname} {nominator_user.user_lastname}".strip()
                except User.DoesNotExist:
                    nominator_name = "Unknown"
                    
                awards_dict[award_id_str]["nominations_information"].append({
                    "nominator": nominator_name,
                    "nomination_date": nom.nomination_date.strftime("%Y-%m-%d") if nom.nomination_date else nom.created_at.strftime("%Y-%m-%d"),
                    "comments": nom.comments
                })
            
            list_of_awards = list(awards_dict.values())
            
            # Add to leaderboard if they have points or awards
            if (user.no_of_points and user.no_of_points > 0) or list_of_awards:
                leaderboard.append({
                    "employeename": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "image": user.user_image.url if user.user_image else "",
                    "total_awards": user.no_of_awards or 0,
                    "total_no_of_points": user.no_of_points or 0,
                    "List_of_awards": list_of_awards
                })
                
        # Sort leaderboard by total_no_of_points in descending order
        leaderboard.sort(key=lambda x: x["total_no_of_points"], reverse=True)
        
        return Response(leaderboard, status=status.HTTP_200_OK)

class get_admin_dashboard_details_view(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        try:
            total_users = User.objects.exclude(user_role__in=["Admin","Art Manager"]).count()
            total_arts = ARTTable.objects.count()
            total_teams = TeamsTable.objects.count()
            all_time_nominations = NominationsTable.objects.count()
            ##TODO have total_employess and total_art_managers 
            response_data = {
                "total_users": total_users,
                "total_arts": total_arts,
                "total_teams": total_teams,
                "all_time_nominations": all_time_nominations,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_pending_art_managers_view(APIView):
    ##TODO
    ##add admin request under admin dashboard
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        try:
            user_ids_of_managers = User.objects.filter(user_role="Art Manager", is_active=False)
            response_data = []
            for user in user_ids_of_managers:
                response_data.append({
                    "user_id": str(user.user_id),
                    "user_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "user_role": "Art Manager",
                    "status": "Pending"
                })            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_registered_art_managers_view(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    def get(self, request):
        try:
            # Fetch all users with the role 'Art Manager'
            art_managers = User.objects.filter(user_role="Art Manager",is_active=True)
            
            response_data = []
            for manager in art_managers:
                user_name = f"{manager.user_firstname} {manager.user_lastname}".strip()
                status_text = "Active" if manager.is_active else "Pending"
                
                response_data.append({
                    "user_name": user_name,
                    "user_role": manager.user_role,
                    "status": status_text,
                    "user_login": manager.user_login,
                    "art_name": ARTTable.objects.filter(user__user_id=manager.user_id).values_list('art_name', flat=True).first() or "N/A",
                    "department": ARTTable.objects.filter(user__user_id=manager.user_id).values_list('department', flat=True).first() or "N/A"
                })
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_pending_art_employees_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        user_id =  request.user.user_id
        print("User ID from request:", user_id)  # Debugging statement
        print("ART ID from query params:", art_id)  # Debugging statement
        if not art_id  or not user_id:
            return Response({"error": "art_id and user_id are required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        response_data = []
        try:
            if (not ARTTable.objects.filter(art_id=art_id,user__user_id=user_id).exists()):
                return Response({"error": "ART not found or User is not part of the ART"}, status=status.HTTP_404_NOT_FOUND)
            teams_ids = TeamsTable.objects.filter(art=art_id).values_list('team_id', flat=True)            
            inactive_team_members = TeamMembersTable.objects.filter(team__team_id__in=teams_ids, is_active=0)
            for member in inactive_team_members:
                user = member.user
                response_data.append({
                    "employee_id": str(member.employee_id),
                    "team_id": str(member.team.team_id),
                    "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "team_name": member.team.team_name,
                    "employee_role": user.user_role,
                    "image": user.user_image.url if user.user_image else "",
                    "active_status": "Pending"
                })
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_art_employees_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        response = Service.get_art_employees(request)
        return CommonService.CustomResponse(response)

class manage_award_view(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]

        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminUser()]
        
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        
        if self.request.method == 'PUT':
            return [IsAuthenticated(), IsAdminUser()]

        return [IsAuthenticated()]
    
    def get(self, request):
        response = Service.get_awards()
        return CommonService.CustomResponse(response)


    def post(self, request):
        response = Service.create_award(request)
        return CommonService.CustomResponse(response)
    
    def put(self, request):
        response = Service.update_award(request)
        return CommonService.CustomResponse(response)
    
    def delete(self, request):
        response = Service.delete_award(request)
        return CommonService.CustomResponse(response)
        
        
class update_art_manager_request_view(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    def put(self, request):
        response = Service.update_art_manager_request(request)
        return CommonService.CustomResponse(response)
        
class get_user_employee_details_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        response = Service.get_user_employee_details(request)
        return CommonService.CustomResponse(response)

class get_arts_and_teams_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        response = Service.get_arts_and_teams()
        return CommonService.CustomResponse(response)

class get_user_home_page_data_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        response = Service.get_user_home_page_data(request)
        return CommonService.CustomResponse(response)