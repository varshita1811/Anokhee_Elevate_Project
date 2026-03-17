from django.contrib import admin
from django.urls import path
from .views import *


urlpatterns=[
    path("art/",manage_art_view.as_view()),
    path('teams/', manage_teams_view.as_view()),
    path('team-members/', manage_team_member_view.as_view()),
    path('sprint/', manage_sprint_view.as_view()),
    path('users/', manage_user_view.as_view()),
    path('nomination-data/', get_nomination_data_view.as_view()),
    path('nomination/', create_nomination_view.as_view()),
    path('leaderboard-art/', get_leaderboard_art_level_view.as_view()),
    path('leaderboard-team/', get_leaderboard_team_level_view.as_view()),
    path('admin-dashboard/', get_admin_dashboard_details_view.as_view()),##done
    path('pending-art-managers/', get_pending_art_managers_view.as_view()), ##done
    path('registered-art-managers/', get_registered_art_managers_view.as_view()), ##done
    path('pending-art-employees/', get_pending_art_employees_view.as_view()),##done
    path('art-employees/', get_art_employees_view.as_view()),
    path('awards/', manage_award_view.as_view()),
    path('get-current-sprint/', get_current_sprint_view.as_view()),
    path('update-art-manager-request/', update_art_manager_request_view.as_view()),
    path('get-user-employee-details/', get_user_employee_details_view.as_view()),
    path('get-arts-and-teams/', get_arts_and_teams_view.as_view()),
    path('get-user-home-page-data/', get_user_home_page_data_view.as_view()), 


]