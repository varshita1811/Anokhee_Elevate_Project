from django.db import models

# Create your models here.
from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, user_login, password=None, user_role="Employee",user_firstname=None, user_lastname=None,user_image=None):
        if not user_login or not user_firstname or not user_lastname:
            raise ValueError("User login, first name, and last name are required")

        user = self.model(
            user_login=user_login,
            user_role=user_role,
            user_firstname=user_firstname,
            user_lastname=user_lastname,
            user_image=user_image,
            no_of_points=0,
            no_of_awards=0
        )
        user.set_password(password) 

        if user_role == "Admin" or user_role == "Art Manager":
            user.is_active = False
            user.is_staff = True
        else:
            user.is_active = True
            user.is_staff = False
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    alphanumeric_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9]+$', 
        message='This field can only contain alphanumeric characters (a-z, A-Z, 0-9). No spaces or special characters allowed.'
    )
    alphanumeric_space_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9 ]+$', 
        message='This field can only contain alphanumeric characters (a-z, A-Z, 0-9) and spaces. No special characters allowed.'
    )

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_login = models.CharField(max_length=200, unique=True, validators=[alphanumeric_validator])##ldap creds
    user_role = models.CharField(max_length=50) ## here it should display all 14 roles 
    user_firstname = models.CharField(max_length=100, null=False, validators=[alphanumeric_space_validator])
    user_lastname = models.CharField(max_length=100, null=False, validators=[alphanumeric_space_validator])
    user_image = models.CharField(max_length=500, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    no_of_points = models.IntegerField(null=True, default=0)
    no_of_awards = models.IntegerField(null=True, default=0)
    


    objects = UserManager()

    USERNAME_FIELD = 'user_login'
    REQUIRED_FIELDS = []

class ARTTable(models.Model):
    art_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    art_name = models.CharField(max_length=200, unique=True)
    user = models.OneToOneField(User, to_field='user_id',null=False, on_delete=models.CASCADE, related_name='art_manager_user',default=None)
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TeamsTable(models.Model):
    team_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_name = models.CharField(max_length=200)
    team_description = models.CharField(max_length=500, null=True)
    art = models.ForeignKey(ARTTable, to_field='art_id', on_delete=models.CASCADE, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TeamMembersTable(models.Model):
    employee_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(TeamsTable, to_field='team_id', on_delete=models.CASCADE, related_name='members')
    user = models.OneToOneField(User, to_field='user_id', on_delete=models.CASCADE, related_name='team_member',default=None)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SprintTable(models.Model):
    sprint_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint_name = models.CharField(max_length=50)
    art = models.ForeignKey(ARTTable, to_field='art_id', on_delete=models.CASCADE, related_name='sprints')
    year = models.IntegerField(null=False)
    quater = models.IntegerField(null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    status = models.CharField(max_length=50, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AwardsTable(models.Model):
    award_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    award_name = models.CharField(max_length=200, unique=True)
    award_description = models.TextField()
    award_image = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class NominationsTable(models.Model):
    nomination_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_nominated = models.UUIDField( editable=False)
    sprint = models.ForeignKey(SprintTable, to_field='sprint_id', on_delete=models.CASCADE, related_name='nominations')
    award = models.ForeignKey(AwardsTable, to_field='award_id', on_delete=models.CASCADE, related_name='nominations')
    nominator = models.UUIDField( editable=False)
    comments = models.TextField(null=False)
    nomination_date = models.DateTimeField(auto_now_add=True)
    no_of_nominations_left = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JiraTasksTable(models.Model):
    tasks_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(TeamMembersTable, to_field='employee_id', on_delete=models.CASCADE, related_name='jira_tasks')
    tasks = models.JSONField()
    sprint = models.ForeignKey(SprintTable, to_field='sprint_id', on_delete=models.CASCADE, related_name='jira_tasks')
    no_of_points = models.IntegerField(null=True, default=0)
    no_of_awards = models.IntegerField(null=True, default=0)
