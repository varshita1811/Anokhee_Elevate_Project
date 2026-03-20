
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
                last_sprint_top5_champions_in_your_art = CommonService.get_last_sprint_top5_champions_in_your_art(last_sprint_id,art_id_of_user)


            home_page_data = {
                "last_sprint_top5_champions_in_your_art": last_sprint_top5_champions_in_your_art,
                "art_level_champions_top5": get_art_level_champions_top5(art_id_of_user),
                "organization_level_champions_top5_till_now": get_organization_level_champions_top5_till_now(),
                "total_nominations_done_in_last_day": get_total_nominations_done_in_last_day(),
                "total_active_Employees": get_total_active_employees()
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
        employees = User.objects.filter(user_role="Employee").order_by('-no_of_points')[:5]
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
    
