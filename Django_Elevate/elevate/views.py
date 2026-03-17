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

class manage_user_view(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        role = request.query_params.get('role')
        
        users = User.objects.all()
        if user_id:
            users = users.filter(user_id=user_id)
        if role:
            users = users.filter(user_role=role)
            
        serializer = UserSerializer(users, many=True)
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
    def get(self, request):
        user_id = request.query_params.get('user_id')
        sprint_id = request.query_params.get('sprint_id')
        
        if not user_id or not sprint_id:
            return Response({"error": "user_id and sprint_id are required in query params"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
           
            sprint = SprintTable.objects.get(sprint_id=sprint_id)
            sprint_name = sprint.sprint_name
            
           
            nominations = NominationsTable.objects.filter(nominator=user_id, sprint=sprint_id)
            awards_used = []
            for nom in nominations:
                awards_used.append({
                    "award_id": str(nom.award.award_id),
                    "award_name": nom.award.award_name
                })
                
            # Find User's Team
            try:
                user_team_member = TeamMembersTable.objects.get(user=user_id)
                user_team = user_team_member.team
                art = user_team.art
                
                # 3. User Team Members
                # Exclude the user themselves from their team list
                user_team_members_qs = TeamMembersTable.objects.filter(team=user_team).exclude(user=user_id)
                user_team_members = []
                for member in user_team_members_qs:
                    user_team_members.append({
                        "employee_id": str(member.employee_id),
                        "user_id": str(member.user.user_id),
                        "name": f"{member.user.user_firstname} {member.user.user_lastname}",
                        "team_name": user_team.team_name,
                        "user_image": member.user.user_image
                    })
                    
                # 4. Other Team Members
                other_teams = TeamsTable.objects.filter(art=art).exclude(team_id=user_team.team_id)
                other_team_members_qs = TeamMembersTable.objects.filter(team__in=other_teams)
                other_team_members = []
                for member in other_team_members_qs:
                    other_team_members.append({
                        "employee_id": str(member.employee_id),
                        "user_id": str(member.user.user_id),
                        "name": f"{member.user.user_firstname} {member.user.user_lastname}",
                        "team_name": member.team.team_name,
                        "user_image": member.user.user_image
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
    def post(self, request):
        user_id = request.data.get('user_id')
        nominated_employee_id = request.data.get('nominated_employee_id')
        award_id = request.data.get('award_id')
        comments = request.data.get('comments')
        sprint_id = request.data.get('sprint_id')
        
        if not all([user_id, nominated_employee_id, award_id, comments]):
            return Response({"error": "user_id, nominated_employee_id, award_id, and comments are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Validate Nominator
            nominator = User.objects.get(user_id=user_id)
            
            # 2. Validate Nominated Employee
            nominated_employee = TeamMembersTable.objects.get(employee_id=nominated_employee_id)
            nominated_user = nominated_employee.user
            
            # 3. Validate Award
            award = AwardsTable.objects.get(award_id=award_id)
            
            # 4. Get or infer Sprint
            if sprint_id:
                sprint = SprintTable.objects.get(sprint_id=sprint_id)
            else:
                sprint = SprintTable.objects.filter(art=nominated_employee.team.art).order_by('-created_at').first()
                if not sprint:
                    return Response({"error": "No sprint found. Please provide sprint_id."}, status=status.HTTP_400_BAD_REQUEST)
                    
            # 5. Check nominations left
            nominations_made = NominationsTable.objects.filter(nominator=nominator.user_id, sprint=sprint).count()
            nominations_left = 5 - nominations_made
            if nominations_left <= 0:
                return Response({"error": "You have exhausted your 5 nominations for this sprint."}, status=status.HTTP_400_BAD_REQUEST)
                
            # 6. Create Nomination
            nomination = NominationsTable.objects.create(
                employee_nominated=nominated_employee.employee_id,
                nominator=nominator.user_id,
                award=award,
                sprint=sprint,
                comments=comments,
                no_of_nominations_left=nominations_left - 1
            )
            
            # 7. Update User table
            points_to_add = int(request.data.get('points', 10)) 
            nominated_user.no_of_awards = (nominated_user.no_of_awards or 0) + 1
            nominated_user.no_of_points = (nominated_user.no_of_points or 0) + points_to_add
            nominated_user.save()
            
            # 8. Update JiraTasksTable
            jira_task = JiraTasksTable.objects.filter(employee=nominated_employee, sprint=sprint).first()
            if jira_task:
                jira_task.no_of_awards = (jira_task.no_of_awards or 0) + 1
                jira_task.no_of_points = (jira_task.no_of_points or 0) + points_to_add
                jira_task.save()
                
            return Response({
                "message": "Nomination created successfully",
                "data": {
                    "nomination_id": str(nomination.nomination_id),
                    "no_of_nominations_left": nomination.no_of_nominations_left
                }
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
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
    def get(self, request):
        try:
            total_users = User.objects.count()
            total_arts = ARTTable.objects.count()
            total_teams = TeamsTable.objects.count()
            all_time_nominations = NominationsTable.objects.count()
            
            # Additional helpful stats for the admin dashboard
            total_sprints = SprintTable.objects.count()
            total_awards_types = AwardsTable.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            response_data = {
                "total_users": total_users,
                "total_arts": total_arts,
                "total_teams": total_teams,
                "all_time_nominations": all_time_nominations,
                "total_sprints": total_sprints,
                "total_awards_types": total_awards_types,
                "active_users": active_users
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
    def get(self, request):
        try:
            # According to User model, Art Managers start with is_active=False until approved by Admin
            pending_managers = User.objects.filter(user_role="Art Manager", is_active=False)
            
            response_data = []
            for manager in pending_managers:
                manager_name = f"{manager.user_firstname} {manager.user_lastname}".strip()
                
                # Check if this manager is already linked to an ART
                # If they are just registering, they might not have an ARTTable entry yet
                art_name = "Not Assigned"
                department = "Not Assigned"
                
                try:
                    art = ARTTable.objects.get(user=manager)
                    art_name = art.art_name
                    department = art.department
                except ARTTable.DoesNotExist:
                    pass
                
                response_data.append({
                    "user_id": str(manager.user_id),
                    "art_manager": manager_name,
                    "art_name": art_name,
                    "department": department,
                    "user_login": manager.user_login
                })
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_registered_art_managers_view(APIView):
    def get(self, request):
        try:
            # Fetch all users with the role 'Art Manager'
            art_managers = User.objects.filter(user_role="Art Manager")
            
            response_data = []
            for manager in art_managers:
                user_name = f"{manager.user_firstname} {manager.user_lastname}".strip()
                status_text = "Active" if manager.is_active else "Pending"
                
                response_data.append({
                    "user_id": str(manager.user_id),
                    "user_name": user_name,
                    "user_role": manager.user_role,
                    "status": status_text,
                    "user_login": manager.user_login
                })
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_pending_art_employees_view(APIView):
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # First fetch all team members associated with teams in this ART
            team_members = TeamMembersTable.objects.filter(team__art=art_id).select_related('user', 'team')
            
            response_data = []
            for member in team_members:
                user = member.user
                
                # Check if the user is inactive (pending approval)
                if not user.is_active:
                    user_name = f"{user.user_firstname} {user.user_lastname}".strip()
                    
                    response_data.append({
                        "user_id": str(user.user_id),
                        "user_name": user_name,
                        "user_role": user.user_role,
                        "team_name": member.team.team_name,
                        "user_login": user.user_login
                    })
                    
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class get_art_employees_view(APIView):
    def get(self, request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return Response({"error": "art_id is required in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Fetch all team members associated with teams in this ART
            team_members = TeamMembersTable.objects.filter(team__art=art_id).select_related('user', 'team')
            
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
