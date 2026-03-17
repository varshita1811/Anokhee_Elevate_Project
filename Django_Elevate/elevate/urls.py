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
    path('admin-dashboard/', get_admin_dashboard_details_view.as_view()),
    path('pending-art-managers/', get_pending_art_managers_view.as_view()),
    path('registered-art-managers/', get_registered_art_managers_view.as_view()),
    path('pending-art-employees/', get_pending_art_employees_view.as_view()),
    path('art-employees/', get_art_employees_view.as_view()),
    path('admins/', get_admins_view.as_view()),


    #art manager - 

    #get- inactive accounts(profiles)
    #get all the profiles from user tables where the account status is inactive/onhold
    #update profile -put (update the profile)


    #update art -(put call)(art_name, department)
    #delete art-(art_id queryparam)
    #get art -get call(art-id queryparam)
    #creating-art (post call)(art_name, department)

    #----teams 
    #create teams (post- team_name, team_despcription, art_id)
    #get teams (get-art_id)
    #update teams (put- team_name, team_despcription, art_id)
    #delete teams (art_id and team_id queryparam)

    #-----team members------
    #create team members -(team_id,emp_firstname, emp_lastname,user_id,user_image,emp_role)
    #update team members -(team_id,emp_firstname, emp_lastname,user_id,user_image,emp_role)
    #get team members-(team_id and user_id queryparam)
    #delete team members-(team_id and employee_id)

    #-----Sprint----
    #create sprint - (post sprint_name,art_id,year,quater,start_date,end_date,status)
    #update sprint- (put sprint_name,art_id,year,quater,start_date,end_date,status)
    #get sprint- (art_id queryparam)
    #delete sprint (sprint_id)


    #get sprint 
    #get award
    #get teams 


    

    


]
