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
        list_art=ARTTable.objects.filter(user__user_id=request.user.user_id)
        if not list_art.exists():
            return Response({"error": "No ARTs found for this user"}, status=status.HTTP_404_NOT_FOUND)
        json_art=art_serializers(list_art,many=True)

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
                    "error": "user_id in request body must match the authenticated user's ID"
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

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                user_login=serializer.validated_data.get('user_login'),
                password=request.data.get('password'),
                user_role=serializer.validated_data.get('user_role', 'Employee'),
                user_firstname=serializer.validated_data.get('user_firstname'),
                user_lastname=serializer.validated_data.get('user_lastname')
            )
       
            user.user_image = serializer.validated_data.get('user_image', user.user_image)
            user.no_of_points = serializer.validated_data.get('no_of_points', user.no_of_points)
            user.no_of_awards = serializer.validated_data.get('no_of_awards', user.no_of_awards)
            if 'is_active' in serializer.validated_data:
                user.is_active = serializer.validated_data.get('is_active')
            if 'is_staff' in serializer.validated_data:
                user.is_staff = serializer.validated_data.get('is_staff')
            user.save()
            return Response(
                {
                    "message": "User created successfully",
                    "data": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        sprint_id = request.query_params.get('sprint_id')
        
        if not user_id or not sprint_id:
            return Response({"error": "user_id and sprint_id are required in query params"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
           
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
            sprint_name = sprint.sprint_name

            employee_id = TeamMembersTable.objects.filter(user__user_id=user_id).values_list('employee_id', flat=True).first()
            
           
            nominations = NominationsTable.objects.filter(nominator=employee_id, sprint=sprint_id)
            awards_used = []
            for nom in nominations:
                awards_used.append({
                    "award_id": str(nom.award.award_id),
                    "award_name": nom.award.award_name
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
                        "employee_image": member.user.user_image
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
                        "employee_image": member.user.user_image
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
        nominator_id = request.data.get('nominator_id')
        nominee_id = request.data.get('nominee_id')
        award_id = request.data.get('award_id')
        comments = request.data.get('comments')
        sprint_id = request.data.get('sprint_id')
        
        if not all([nominator_id, nominee_id, award_id, comments]):
            return Response({"error": "nominator_id, nominee_id, award_id, and comments are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Validate Nominator
            nominator = TeamMembersTable.objects.get(employee_id=nominator_id)

            # 2. Validate Nominated Employee
            nominee_employee = TeamMembersTable.objects.get(employee_id=nominee_id)
            nominee_user = nominee_employee.user
            
            # 3. Validate Award
            award = AwardsTable.objects.get(award_id=award_id)
            
            # 4. Get or infer Sprint
            if sprint_id:
                sprint = SprintTable.objects.get(sprint_id=sprint_id)
            else:
                sprint = SprintTable.objects.filter(art=nominee_employee.team.art).order_by('-created_at').first()
                if not sprint:
                    return Response({"error": "No sprint found. Please provide sprint_id."}, status=status.HTTP_400_BAD_REQUEST)
                    
            # 5. Check nominations left
            nominations_made = NominationsTable.objects.filter(nominator=nominator.employee_id, sprint=sprint,employee_nominated=nominee_employee.employee_id).count()
            nominations_left = 5 - nominations_made
            if nominations_left <= 0:
                return Response({"error": "You have exhausted your 5 nominations for this sprint."}, status=status.HTTP_400_BAD_REQUEST)
                
            # 6. Create Nomination
            nomination = NominationsTable.objects.create(
                employee_nominated=nominee_employee.employee_id,
                nominator=nominator.employee_id,
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
            jira_task = JiraTasksTable.objects.filter(employee=nominee_employee, sprint=sprint).first()
            if jira_task:
                jira_task.no_of_awards = (jira_task.no_of_awards or 0) + 1
                jira_task.no_of_points = (jira_task.no_of_points or 0) + points_to_add
                jira_task.save()
            else:
                JiraTasksTable.objects.create(
                    employee=nominee_employee,
                    sprint=sprint,
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

class get_leaderboard_art_level_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            art = ARTTable.objects.get(art_id=art_id)
        except ARTTable.DoesNotExist:
            return Response({"error": "ART not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get all team members in this ART
        team_members = TeamMembersTable.objects.filter(team__art=art_id).select_related('user')
        
        leaderboard = []
        for member in team_members:
            user = member.user
            
            # Fetch all nominations for this employee
            nominations = NominationsTable.objects.filter(employee_nominated=member.employee_id).select_related('award')
            
            # Group nominations by award
            awards_dict = {}
            for nom in nominations:
                award_id_str = str(nom.award.award_id)
                if award_id_str not in awards_dict:
                    awards_dict[award_id_str] = {
                        "award": nom.award.award_name,
                        "total_nomniations_for_award": 0,
                        "nominations_information": []
                    }
                
                awards_dict[award_id_str]["total_nomniations_for_award"] += 1
                
                # Fetch nominator details
                try:
                    nominator_user = User.objects.get(user_id=nom.nominator)
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
                    "image": user.user_image or "",
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
        team_id = request.query_params.get('team_id')
        if not team_id:
            return Response({"error": "team_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            team = TeamsTable.objects.get(team_id=team_id)
        except TeamsTable.DoesNotExist:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get all team members in this specific team
        team_members = TeamMembersTable.objects.filter(team=team_id).select_related('user')
        
        leaderboard = []
        for member in team_members:
            user = member.user
            
            # Fetch all nominations for this employee
            nominations = NominationsTable.objects.filter(employee_nominated=member.employee_id).select_related('award')
            
            # Group nominations by award
            awards_dict = {}
            for nom in nominations:
                award_id_str = str(nom.award.award_id)
                if award_id_str not in awards_dict:
                    awards_dict[award_id_str] = {
                        "award": nom.award.award_name,
                        "total_nomniations_for_award": 0,
                        "nominations_information": []
                    }
                
                awards_dict[award_id_str]["total_nomniations_for_award"] += 1
                
                # Fetch nominator details
                try:
                    nominator_user = User.objects.get(user_id=nom.nominator)
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
                    "image": user.user_image or "",
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
            total_users = User.objects.count()
            total_arts = ARTTable.objects.count()
            total_teams = TeamsTable.objects.count()
            all_time_nominations = NominationsTable.objects.count()
            
            response_data = {
                "total_users": total_users,
                "total_arts": total_arts,
                "total_teams": total_teams,
                "all_time_nominations": all_time_nominations,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_admins_view(APIView):
    def get(self, request):
        try:
            admins = User.objects.filter(user_role="Admin")
            
            response_data = []
            for admin in admins:
                user_name = f"{admin.user_firstname} {admin.user_lastname}".strip()
                
                response_data.append({
                    "user_name": user_name,
                    "user_role": admin.user_role,
                    "user_status": admin.is_active
                })
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_pending_art_managers_view(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        try:
            user_ids_of_managers = User.objects.filter(user_role="Art Manager", is_active=False)
            response_data = []
            for user in user_ids_of_managers:
                response_data.append({
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
            art_managers = User.objects.filter(user_role="Art Manager")
            
            response_data = []
            for manager in art_managers:
                user_name = f"{manager.user_firstname} {manager.user_lastname}".strip()
                status_text = "Active" if manager.is_active else "Pending"
                
                response_data.append({
                    "user_name": user_name,
                    "user_role": manager.user_role,
                    "status": status_text,
                    "user_login": manager.user_login
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
                    "image": user.user_image or "",
                    "active_status": "Pending"
                })
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_art_employees_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Fetch all team members associated with teams in this ART
            team_members = TeamMembersTable.objects.filter(team__art=art_id,is_active=1).select_related('user', 'team')
            
            response_data = []
            for member in team_members:
                user = member.user
                
                employee_name = f"{user.user_firstname} {user.user_lastname}".strip()
                status_text = "Active" if user.is_active else "Pending"
                
                response_data.append({
                    "employee_id": str(member.employee_id),
                    "employee_name": employee_name,
                    "team_name": member.team.team_name,
                    "employee_role": user.user_role,
                    "image": user.user_image or "",
                    "total_points": user.no_of_points or 0,
                    "total_awards": user.no_of_awards or 0,
                    "active_status": status_text
                })
                    
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class manage_award_view(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    def get(self, request):
        awards = AwardsTable.objects.all()
        serializer = AwardSerializer(awards, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AwardSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
            )
        try:
            serializer.save()
            return Response(
                {
                    "message": "Award created successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except  Exception as e:
            return Response(
                {"error": "Award with this name already exists"},
                status=status.HTTP_409_CONFLICT
            )
    def put(self, request):
        award_id = request.query_params.get('award_id')
        if not award_id:
            return Response({"error": "award_id is required either in query params or body"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            award = AwardsTable.objects.get(award_id=award_id)
        except AwardsTable.DoesNotExist:
            return Response({"error": "Award not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = AwardSerializer(award, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            serializer.save()
            return Response(
                {
                    "message": "Award updated successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Award with this name already exists"},
                status=status.HTTP_409_CONFLICT
            )
    def delete(self, request):
        award_id = request.query_params.get('award_id')
        if not award_id:
            return Response({"error": "award_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)  
        try:
            award = AwardsTable.objects.get(award_id=award_id)
            award.delete()
            return Response({"message": "Award deleted successfully"}, status=status.HTTP_200_OK)
        except AwardsTable.DoesNotExist:
            return Response({"error": "Award not found with the provided award_id"}, status=status.HTTP_404_NOT_FOUND)
        

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
        
class update_art_manager_request_view(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    def put(self, request):
        if request.user.user_role != "Admin":
            return Response(
                {
                    "error": "Only Admins are allowed to update Art Manager request status"
                },
                status=403
            )
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        art_manager_id = request.data.get('art_manager_id')
        status_to_update = request.data.get('status')
        if not art_manager_id or status_to_update not in ["Approved", "Rejected"]:
            return Response(
                {"error": "art_manager_id and valid status (Approved/Rejected) are required in the request body"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(user_id=art_manager_id, user_role="Art Manager")
            if status_to_update == "Approved":
                user.is_active = True
                user.save()
                return Response({"message": "Art Manager request approved successfully"}, status=status.HTTP_200_OK)
            else:
                user.delete()
                return Response({"message": "Art Manager request rejected and user deleted successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Art Manager user not found with the provided art_manager_id"}, status=status.HTTP_404_NOT_FOUND)
        
class get_user_employee_details_view(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_id = request.user.user_id
        if not user_id:
            return Response({"error": "user_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            team_member = TeamMembersTable.objects.select_related('user', 'team').get(user__user_id=user_id)
            user = team_member.user
            employee_details = {
                "employee_id": str(team_member.employee_id),
                "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                "team_name": team_member.team.team_name,
                "employee_role": user.user_role,
                "image": user.user_image or "",
                "total_points": user.no_of_points or 0,
                "total_awards": user.no_of_awards or 0,
                "active_status": "Active" if user.is_active else "Pending"
            }
            return Response(employee_details, status=status.HTTP_200_OK)
        except TeamMembersTable.DoesNotExist:
            return Response({"error": "Employee details not found for the provided user_id"}, status=status.HTTP_404_NOT_FOUND)