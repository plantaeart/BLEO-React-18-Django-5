from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.logger import Logger
from utils.mongodb_utils import MongoDB
from api.serializers import DebugLogSerializer
from models.enums.LogType import LogType
from datetime import datetime, timedelta

class LoggingView(APIView):
    """API endpoint for client-side logging"""
    
    def post(self, request, format=None):
        """Create a new log entry"""
        serializer = DebugLogSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid log data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Use the Logger utility to save the log
        if data['type'] == LogType.ERROR.value:
            log_id = Logger.error(
                message=data['message'],
                code=data['code'],
                bleoid=data.get('BLEOId'),
                error_source=data.get('error_source')
            )
        else:
            log_id = Logger.user_action(
                bleoid=data.get('BLEOId'),
                message=data['message'],
                log_type=data['type'],
                code=data['code']
            )
        
        if log_id:
            return Response({"success": True, "log_id": str(log_id)}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "Failed to create log entry"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminLogsView(APIView):
    """API endpoint for retrieving logs (admin use only)"""
    
    def get(self, request, format=None):
        """Get logs with optional filtering"""
        try:
            db = MongoDB.get_instance().get_collection('DebugLogs')
            
            # Parse query parameters for filtering
            limit = int(request.query_params.get('limit', 100))
            skip = int(request.query_params.get('skip', 0))
            log_type = request.query_params.get('type')
            bleoid = request.query_params.get('bleoid')
            error_source = request.query_params.get('error_source')
            user_type = request.query_params.get('user_type')
            
            # Date range filtering
            days = request.query_params.get('days')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Build query filters
            query = {}
            
            # Type filter
            if log_type:
                query['type'] = log_type
            
            # BLEOId filter
            if bleoid:
                query['BLEOId'] = bleoid
                
            # Error source filter
            if error_source:
                query['error_source'] = error_source
                
            # User type filter - Add this block
            if user_type:
                query['user_type'] = user_type
            
            # Date filters
            if days:
                try:
                    days_ago = datetime.now() - timedelta(days=int(days))
                    query['date'] = {'$gte': days_ago}
                except ValueError:
                    pass
            
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date)
                    if 'date' not in query:
                        query['date'] = {}
                    query['date']['$gte'] = start
                except ValueError:
                    pass
                    
            if end_date:
                try:
                    end = datetime.fromisoformat(end_date)
                    if 'date' not in query:
                        query['date'] = {}
                    query['date']['$lte'] = end
                except ValueError:
                    pass
                
            # Execute query with pagination
            logs = list(db.find(query).sort('date', -1).skip(skip).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                log['_id'] = str(log['_id'])
                
            return Response({
                'total': db.count_documents(query),
                'logs': logs
            })
            
        except Exception as e:
            Logger.server_error(f"Error retrieving logs: {str(e)}")
            return Response(
                {"error": "Failed to retrieve logs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminLogDetailView(APIView):
    """API endpoint for retrieving a specific log by ID"""
    
    def get(self, request, log_id, format=None):
        """Get a specific log by ID"""
        try:
            db = MongoDB.get_instance().get_collection('DebugLogs')
            
            try:
                log_id_int = int(log_id)
            except ValueError:
                return Response(
                    {"error": "Invalid log ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            log = db.find_one({"id": log_id_int})
            
            if not log:
                return Response(
                    {"error": f"Log with ID {log_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Convert ObjectId to string for JSON serialization
            log['_id'] = str(log['_id'])
            
            return Response(log)
            
        except Exception as e:
            Logger.server_error(f"Error retrieving log: {str(e)}")
            return Response(
                {"error": "Failed to retrieve log"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )