from rest_framework import serializers
from .models import *

class art_serializers(serializers.ModelSerializer):
    class Meta:
        model=ARTTable
        fields="__all__"

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMembersTable
        fields ="__all__"

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamsTable
        fields = "__all__"

class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprintTable
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardsTable
        fields = "__all__"
