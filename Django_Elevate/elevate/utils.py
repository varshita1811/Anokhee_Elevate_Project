from rest_framework import status
from rest_framework.response import Response 
from datetime import datetime, timedelta
from .models import SprintTable

class CommonService:
    @staticmethod
    def success(data={}, message="Success", status_code=status.HTTP_200_OK):
        return {
            "success": True,
            "message": message,
            "data": data,
            "status": status_code
        }
    
    @staticmethod
    def error(message="Error",status_code=status.HTTP_400_BAD_REQUEST, data=None):
        return {
            "success": False,
            "message": message,
            "data": data,
            "status": status_code
        }

    @staticmethod
    def CustomResponse(response):
        if response["success"]:
            return Response(response["data"], status=response["status"])
        else:
            return Response({"error": response["message"]}, status=response["status"])

    @staticmethod
    def get_cache_timeout_for_leaderboard(sprint_id):

        sprint = SprintTable.objects.filter(sprint_id=sprint_id).first()
        if not sprint:
            return 900  # Default timeout if sprint not found

        end_date = sprint.end_date
        now = datetime.now().date()
        print("now:", now, "end_date:", end_date)

        if end_date <= now + timedelta(days=3):
            return 300  # 5 minutes
        elif end_date <= now + timedelta(days=7):
            return 600  # 10 minutes
        else:
            return 900  # 15 minutes