
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import status
from django.db.models import Count
from .utils import *


class Service:
    @staticmethod
    def get_nomination_data(request):
        user_id = request.user.user_id
        teammember = TeamMembersTable.objects.filter(user__user_id=user_id).first()
        team_art = teammember.team.art if teammember else None
        
        sprint_id = SprintTable.objects.filter(art=team_art,status='Active').values_list('sprint_id', flat=True).first()
        if sprint_id is None:
            return CommonService.error("No active sprint found for the user's ART",status_code=status.HTTP_400_BAD_REQUEST)
            
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
            
            return_data ={
                "sprint_name": sprint_name,
                "awards_already_used": awards_used,
                "user_team_members": user_team_members,
                "other_team_members": other_team_members
            }

            return CommonService.success(return_data,)
        
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @staticmethod
    def create_nomination(request):
        nominator_id = request.data.get('nominator_id').replace("-","") if request.data.get('nominator_id') else None
        nominee_id = request.data.get('nominee_id').replace("-","") if request.data.get('nominee_id') else None
        sprint_id = request.data.get('sprint_id').replace("-","") if request.data.get('sprint_id') else None
        award_id = request.data.get('award_id') if request.data.get('award_id') else None
        comments = request.data.get('comments')
        if not all([nominator_id, nominee_id, award_id, comments]):
            return CommonService.error("nominator_id, nominee_id, award_id, and comments are required",status_code=status.HTTP_400_BAD_REQUEST)

        if TeamMembersTable.objects.filter(user__user_id=request.user.user_id,employee_id=nominator_id).exists() is False:
            return CommonService.error("You can only nominate if using your creds.",status_code=status.HTTP_403_FORBIDDEN)

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
                    return CommonService.error("No sprint found. Please provide sprint_id.",status_code=status.HTTP_400_BAD_REQUEST)
            print("Sprint:", sprint)
            print("Nominee Employee ID:", nominee.employee_id)
            print("Nominator Employee ID:", nominator.employee_id) 
            # 5. Check nominations left
            nominations_made = NominationsTable.objects.filter(nominator=nominator, sprint=sprint, nominee=nominee).count()
            print("Nominations Made:", nominations_made)
            nominations_left = 5 - nominations_made
            if nominations_left <= 0:
                return CommonService.error("You have exhausted your 5 nominations for this sprint.",status_code=status.HTTP_400_BAD_REQUEST)
                
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
            return CommonService.success(data = {"nomination_id": str(nomination.nomination_id),"no_of_nominations_left": nominations_left-1},message="Nomination created successfully")
            
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_current_sprint(request):
        team = TeamMembersTable.objects.filter(user__user_id=request.user.user_id).select_related('team').first()
        art_id = TeamsTable.objects.filter(team_id=team.team_id).values_list('art_id', flat=True).first() if team else None
        if not art_id:
            return CommonService.error("art_id is required in query parameters",status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_sprint = SprintTable.objects.filter(art=art_id, status="Active").first()
            if not current_sprint:
                return CommonService.error("No active sprint found for this ART", status_code=status.HTTP_404_NOT_FOUND)
            
            serializer = SprintSerializer(current_sprint)
            return CommonService.success(serializer.data)
            
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @staticmethod
    def get_leaderboard_art_level(request):
        art_id = request.query_params.get('art_id')
        if not art_id or ARTTable.objects.filter(art_id=art_id).first() is None:
            return CommonService.error("art_id is invalid or not provided",status_code=status.HTTP_400_BAD_REQUEST)
        
        get_current_sprint_view_instance = Service.get_current_sprint()
        sprint_response = get_current_sprint_view_instance.get(request)
        if sprint_response.status_code != 200: 
            return CommonService.error("Could not fetch current sprint information",status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sprint_id = sprint_response.data.get("sprint_id")
        if not sprint_id:
            return CommonService.error("No active sprint found for the user's ART",status_code=status.HTTP_400_BAD_REQUEST)
        
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
        return CommonService.success(leaderboard)


    @staticmethod
    def get_leaderboard_team_level(request):
        team_id = TeamMembersTable.objects.filter(user__user_id=request.user.user_id).values_list('team__team_id', flat=True).first()
        if not team_id or team_id is None:
            return CommonService.error("team_id is required in query parameters",status_code=status.HTTP_400_BAD_REQUEST)
        
        get_current_sprint_view_instance = Service.get_current_sprint()
        sprint_response = get_current_sprint_view_instance.get(request)
        if sprint_response.status_code != 200: 
            return CommonService.error("Could not fetch current sprint information",status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sprint_id = sprint_response.data.get("sprint_id")
        if not sprint_id:
            return CommonService.error("No active sprint found for the user's ART",status=status.HTTP_400_BAD_REQUEST)


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

        return CommonService.success(leaderboard)
    

    @staticmethod
    def get_pending_art_managers(request):
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
            return CommonService.success(response_data)          
            
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_admin_dashboard_details(request):
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
            return CommonService.success(response_data)
            
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def get_registered_art_managers(request):
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
            return CommonService.success(response_data)    
        except Exception as e:
            return CommonService.error(str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_pending_art_employees(request):
        art_id = request.query_params.get('art_id')
        user_id =  request.user.user_id
        if not art_id  or not user_id:
            return CommonService.error(message="art_id and user_id are required in query parameters",status_code=status.HTTP_400_BAD_REQUEST)
        response_data = []
        try:
            if (not ARTTable.objects.filter(art_id=art_id,user__user_id=user_id).exists()):
                return CommonService.error(message="ART not found or User is not part of the ART",status_code=status.HTTP_404_NOT_FOUND)
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
            return CommonService.success(response_data)
        except Exception as e:
            return CommonService.error(message= str(e),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

    @staticmethod
    def get_art_employees(request):
        art_id = request.query_params.get('art_id')
        if not art_id:
            return CommonService.error(message="art_id is required in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
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
                    "image": user.user_image.url if user.user_image else "",
                    "total_points": user.no_of_points or 0,
                    "total_awards": user.no_of_awards or 0,
                    "active_status": status_text
                })
                    
            return CommonService.success(data=response_data)
            
        except Exception as e:
            return CommonService.error(message="An error occurred while fetching ART employees: " + str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_awards():
        try:
            awards = AwardsTable.objects.all()
            serializer = AwardSerializer(awards, many=True)
            return CommonService.success(data=serializer.data)
        except Exception as e:
            return CommonService.error(message="An error occurred while fetching awards: " + str(e))
    
    @staticmethod
    def create_award(request):
        serializer = AwardSerializer(data=request.data)
        if not serializer.is_valid():
            return CommonService.error(message="Invalid award data", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return CommonService.success(data=serializer.data)
        except  Exception as e:
            return CommonService.error(message="Award with this name already exists", status_code=status.HTTP_409_CONFLICT)

    @staticmethod
    def update_award(request):
        award_id = request.query_params.get('award_id')
        if not award_id:
            return CommonService.error(message="award_id is required either in query params or body", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            award = AwardsTable.objects.get(award_id=award_id)
        except AwardsTable.DoesNotExist:
            return CommonService.error(message="Award not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = AwardSerializer(award, data=request.data, partial=True)
        if not serializer.is_valid():
            return CommonService.error(message="Invalid award data", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return CommonService.success(data=serializer.data)
        except Exception as e:
            return CommonService.error(message="Award with this name already exists", status_code=status.HTTP_409_CONFLICT)
    
    @staticmethod
    def delete_award(request):
        award_id = request.query_params.get('award_id')
        if not award_id:
            return CommonService.error(message="award_id is required in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            award = AwardsTable.objects.get(award_id=award_id)
            award.delete()
            return CommonService.success(message="Award deleted successfully")
        except AwardsTable.DoesNotExist:
            return CommonService.error(message="Award not found", status_code=status.HTTP_404_NOT_FOUND)
        
    @staticmethod
    def get_user_home_page_data(request):
        user_id = request.user.user_id
        last_sprint_top5_champions_in_your_art=[]
        last_sprint_id = None
        art_id_of_user = None
        try:
            ##if user role is Art Manager then
            if request.user.user_role == "Art Manager":
                art_id_of_user = ARTTable.objects.filter(user__user_id=user_id).values_list('art_id', flat=True).first()
            else:
                art_id_of_user = TeamMembersTable.objects.filter(user__user_id=user_id).values_list('team__art_id', flat=True).first()
 
            if art_id_of_user:
                last_sprint_id = SprintTable.objects.filter(art=art_id_of_user, status="Completed").values_list('sprint_id', flat=True).order_by('-end_date').first()
            if last_sprint_id: 
                last_sprint_top5_champions_in_your_art = get_last_sprint_top5_champions_in_your_art(last_sprint_id,art_id_of_user)


            home_page_data = {
                "last_sprint_top5_champions_in_your_art": last_sprint_top5_champions_in_your_art,
                "art_level_champions_top5": get_art_level_champions_top5(art_id_of_user),
                "organization_level_champions_top5_till_now": get_organization_level_champions_top5_till_now(),
                "total_nominations_done_in_last_day": get_total_nominations_done_in_last_day(),
                "total_active_Employees": get_total_active_employees(),
                "is_manager": request.user.user_role == "Manager"
            }
            return CommonService.success(data=home_page_data)
        except User.DoesNotExist:
            return CommonService.error(message="User not found with the provided user_id")
    
    @staticmethod
    def get_arts_and_teams():
        try:
            arts = ARTTable.objects.all()
            response_data = []
            for art in arts:
                teams = TeamsTable.objects.filter(art=art).values('team_id', 'team_name')
                response_data.append({
                    "art_id": str(art.art_id),
                    "art_name": art.art_name,
                    "art_manager": f"{art.user.user_firstname} {art.user.user_lastname}".strip() if art.user else "N/A",
                    "department": art.department,
                    "teams": list(teams)
                })
            return CommonService.success(data=response_data)
        except Exception as e:
            return CommonService.error(message="An error occurred while fetching arts and teams data: " + str(e))
    
    @staticmethod
    def get_user_employee_details(request):
        user_id = request.user.user_id

        if not user_id:
            return CommonService.error(message="user_id is required in query parameters", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            if not TeamMembersTable.objects.filter(user__user_id=user_id).exists():
                user = User.objects.get(user_id=user_id)
                employee_details = {
                    "employee_id": None,
                    "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "team_name": None,
                    "employee_role": user.user_role,
                    "image": user.user_image.url if user.user_image else "",
                    "art_id": None,
                    "art_name": None,
                    "total_points": user.no_of_points or 0,
                    "total_awards": user.no_of_awards or 0,
                    "active_status": "No Request Pending"
                }
            else:
                team_member = TeamMembersTable.objects.select_related('user', 'team').get(user__user_id=user_id)
                user = team_member.user if team_member else None
                art = team_member.team.art if team_member.team else None
                employee_details = {
                    "employee_id": str(team_member.employee_id),
                    "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                    "team_name": team_member.team.team_name if team_member.team else None, 
                    "employee_role": user.user_role if user else None,
                    "image": user.user_image.url if user and user.user_image else "",
                    "art_id": str(art.art_id) if art else None,
                    "art_name": art.art_name if art else None,
                    "total_points": user.no_of_points or 0 if user else 0,
                    "total_awards": user.no_of_awards or 0 if user else 0,
                    "active_status": "Active" if team_member.is_active else "Request Pending"
                }
            return CommonService.success(data=employee_details)
        except TeamMembersTable.DoesNotExist:
            return CommonService.error(message="Employee details not found for the provided user_id")
    
    @staticmethod
    def update_art_manager_request(request):
        if request.user.user_role != "Admin":
            return CommonService.error(message="Only Admins are allowed to update Art Manager request status", status_code=status.HTTP_403_FORBIDDEN)

        art_manager_id = request.query_params.get('art_manager_id')
        status_to_update = request.data.get('status')
        if not art_manager_id or status_to_update not in ["Approved", "Rejected"]:
            return CommonService.error(message="art_manager_id and valid status (Approved/Rejected) are required in the request body", status_code=status.HTTP_400_BAD_REQUEST )
        try:
            user = User.objects.get(user_id=art_manager_id, user_role="Art Manager")
            if status_to_update == "Approved":
                user.is_active = True
                user.save()
                return CommonService.success(message="Art Manager request approved successfully")
            else:
                user.delete()
                return CommonService.success(message="Art Manager request rejected and user deleted successfully")
        except User.DoesNotExist:
            return CommonService.error(message="Art Manager user not found with the provided art_manager_id", status_code=status.HTTP_404_NOT_FOUND)

def get_last_sprint_top5_champions_in_your_art(sprint_id,art_id):
        employees = JiraTasksTable.objects.filter(sprint__sprint_id=sprint_id, team__art=art_id).order_by('-no_of_points')[:5]
        last_sprint_top5_champions_in_your_art =[]
        for emp in employees:
            most_received_award_name = NominationsTable.objects.filter(nominee=emp.employee.employee_id,sprint__sprint_id=sprint_id).values('award__award_name').annotate(count=Count('award')).order_by('-count').first()
            most_received_award_name = most_received_award_name['award__award_name'] if most_received_award_name else "N/A"
            user = emp.employee.user
            last_sprint_top5_champions_in_your_art.append({
                "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                "employee_image": user.user_image.url if user.user_image else "",
                "no_of_nominations_received": emp.no_of_awards or 0,
                "most_received_award_name": most_received_award_name,
            })
        return last_sprint_top5_champions_in_your_art

def get_art_level_champions_top5(art_id):
        employees = JiraTasksTable.objects.filter(team__art=art_id).order_by('-no_of_points')[:5]
        art_level_champions_top5 =[]
        for emp in employees:
            most_received_award_name = NominationsTable.objects.filter(nominee=emp.employee.employee_id).values('award__award_name').annotate(count=Count('award')).order_by('-count').first()
            most_received_award_name = most_received_award_name['award__award_name'] if most_received_award_name else "N/A"
            user = emp.employee.user
            art_level_champions_top5.append({
                "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                "employee_image": user.user_image.url if user.user_image else "",
                "no_of_nominations_received": emp.no_of_awards or 0,
                "most_received_award_name": most_received_award_name,
            })
        return art_level_champions_top5

def get_organization_level_champions_top5_till_now():
        employees = User.objects.filter(is_staff=False, is_active=True).order_by('-no_of_points')[:5]
        organization_level_champions_top5_till_now =[]
        for user in employees:
            most_received_award_name = NominationsTable.objects.filter(nominee__in=TeamMembersTable.objects.filter(user=user).values_list('employee_id', flat=True)).values('award__award_name').annotate(count=Count('award')).order_by('-count').first()
            most_received_award_name = most_received_award_name['award__award_name'] if most_received_award_name else "N/A"
            team_member = TeamMembersTable.objects.filter(user=user).select_related('team__art').first()
            organization_level_champions_top5_till_now.append({
                "employee_name": f"{user.user_firstname} {user.user_lastname}".strip(),
                "employee_image": user.user_image.url if user.user_image else "",
                "no_of_nominations_received": user.no_of_awards or 0,
                "team_name": team_member.team.team_name if team_member else "N/A",
                "art_name": team_member.team.art.art_name if team_member and team_member.team.art else "N/A",
                "department": team_member.team.art.department if team_member and team_member.team.art else "N/A",
                "most_received_award_name": most_received_award_name,
            })
        return organization_level_champions_top5_till_now

def get_total_nominations_done_in_last_day():
        last_day = timezone.now() - timedelta(days=1)
        total_nominations_done_in_last_day = NominationsTable.objects.filter(created_at__gte=last_day).count()
        return total_nominations_done_in_last_day
    
def get_total_active_employees():
    total_active_employees = User.objects.filter(is_staff=False, is_active=True).count()
    return total_active_employees
    
