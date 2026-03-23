from rest_framework import status
from rest_framework.response import Response 

class CommonService:
    @staticmethod
    def success(data={}, message="Success", status=status.HTTP_200_OK):
        return {
            "success": True,
            "message": message,
            "data": data,
            "status": status
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
