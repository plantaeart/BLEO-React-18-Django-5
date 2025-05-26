# Create Views/Connection/ConnectionView.py
from rest_framework.views import APIView
from rest_framework import status
from models.response.BLEOResponse import BLEOResponse
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime

class ConnectionStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class ConnectionRequestView(APIView):
    """API view for sending connection requests"""
    
    def post(self, request):
        """Send a connection request"""
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['from_bleoid', 'to_bleoid']
            for field in required_fields:
                if field not in data:
                    return BLEOResponse.validation_error(
                        message=f"Missing required field: {field}"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            from_bleoid = int(data['from_bleoid'])
            to_bleoid = int(data['to_bleoid'])
            
            # Check users exist
            db_users = MongoDB.get_instance().get_collection('Users')
            from_user = db_users.find_one({"BLEOId": from_bleoid})
            to_user = db_users.find_one({"BLEOId": to_bleoid})
            
            if not from_user or not to_user:
                return BLEOResponse.not_found(
                    message="One or both users not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db_links = MongoDB.get_instance().get_collection('Links')
            
            # Check if sender already has an active connection or pending request
            existing_from = db_links.find_one({
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": {"$ne": None},  # Only care about connections to actual users
                "status": {"$in": [ConnectionStatus.PENDING, ConnectionStatus.ACCEPTED]}
            })
            
            if existing_from:
                if existing_from["BLEOIdPartner2"] == to_bleoid:
                    return BLEOResponse.error(
                        error_type="DuplicateError",
                        error_message="You already have a connection request with this user"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                else:
                    return BLEOResponse.error(
                        error_type="LimitExceeded",
                        error_message="You already have an active connection or pending request with someone else"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check if receiver already has an active connection
            existing_to = db_links.find_one({
                "$or": [
                    {"BLEOIdPartner1": to_bleoid, "status": ConnectionStatus.ACCEPTED},
                    {"BLEOIdPartner2": to_bleoid, "status": ConnectionStatus.ACCEPTED}
                ]
            })
            
            if existing_to:
                return BLEOResponse.error(
                    error_type="LimitExceeded",
                    error_message="The user you're trying to connect with already has an active connection"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check for existing rejected/blocked requests - allow overwrite
            existing_rejected = db_links.find_one({
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": to_bleoid,
                "status": {"$in": [ConnectionStatus.REJECTED, ConnectionStatus.BLOCKED]}
            })
            
            if existing_rejected:
                # Update existing rejected connection to pending
                result = db_links.update_one(
                    {"_id": existing_rejected["_id"]},
                    {
                        "$set": {
                            "status": ConnectionStatus.PENDING,
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                updated = db_links.find_one({"_id": existing_rejected["_id"]})
                updated["_id"] = str(updated["_id"])
                
                return BLEOResponse.success(
                    data=updated,
                    message="Connection request renewed"
                ).to_response(status.HTTP_200_OK)
            
            # Create connection request
            link = {
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": to_bleoid,
                "status": ConnectionStatus.PENDING,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result = db_links.insert_one(link)
            
            # Get created link with ID
            created_link = link
            created_link["_id"] = str(result.inserted_id)
            
            return BLEOResponse.success(
                data=created_link,
                message="Connection request sent"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to send connection request: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConnectionResponseView(APIView):
    """API view for responding to connection requests"""
    
    def put(self, request, connection_id):
        """Accept/Reject connection request"""
        try:
            action = request.data.get('action')
            
            if action not in ['accept', 'reject', 'block']:
                return BLEOResponse.validation_error(
                    message="Invalid action. Must be 'accept', 'reject', or 'block'"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get connection
            db_links = MongoDB.get_instance().get_collection('Links')
            connection = db_links.find_one({"_id": ObjectId(connection_id)})
            
            if not connection:
                return BLEOResponse.not_found(
                    message="Connection request not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # If accepting, check if receiver already has an active connection
            if action == 'accept':
                to_bleoid = connection["BLEOIdPartner2"]
                
                # Check if receiver already has an active connection
                existing_to = db_links.find_one({
                    "$and": [
                        {"_id": {"$ne": ObjectId(connection_id)}},  # Exclude current connection
                        {"$or": [
                            {"BLEOIdPartner1": to_bleoid, "status": ConnectionStatus.ACCEPTED},
                            {"BLEOIdPartner2": to_bleoid, "status": ConnectionStatus.ACCEPTED}
                        ]}
                    ]
                })
                
                if existing_to:
                    return BLEOResponse.error(
                        error_type="LimitExceeded",
                        error_message="You already have an active connection with someone else"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Map action to status
            status_map = {
                'accept': ConnectionStatus.ACCEPTED,
                'reject': ConnectionStatus.REJECTED,
                'block': ConnectionStatus.BLOCKED
            }
            
            # Update connection
            result = db_links.update_one(
                {"_id": ObjectId(connection_id)},
                {
                    "$set": {
                        "status": status_map[action],
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count == 0:
                return BLEOResponse.error(
                    error_type="UpdateError",
                    error_message="No changes made"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get updated connection
            updated_connection = db_links.find_one({"_id": ObjectId(connection_id)})
            updated_connection['_id'] = str(updated_connection['_id'])
            
            return BLEOResponse.success(
                data=updated_connection,
                message=f"Connection request {action}ed"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to process connection response: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConnectionListView(APIView):
    """API view for listing user connections"""
    
    def get(self, request):
        """Get all connections for a user"""
        try:
            # Get user ID from query parameters
            bleoid = request.query_params.get('bleoid')
            status_filter = request.query_params.get('status')
            
            if not bleoid:
                return BLEOResponse.validation_error(
                    message="BLEOId parameter is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            try:
                bleoid = int(bleoid)
            except ValueError:
                return BLEOResponse.validation_error(
                    message="BLEOId must be a number"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Build query
            query = {
                "$or": [
                    {"BLEOIdPartner1": bleoid},
                    {"BLEOIdPartner2": bleoid}
                ]
            }
            
            # Add status filter if provided
            if status_filter:
                query["status"] = status_filter
            
            # Get connections
            db_links = MongoDB.get_instance().get_collection('Links')
            connections = list(db_links.find(query))
            
            # Convert ObjectId to str for each connection
            for conn in connections:
                conn['_id'] = str(conn['_id'])
                
                # Add user info for the other party in each connection
                other_id = conn['BLEOIdPartner2'] if conn['BLEOIdPartner1'] == bleoid else conn['BLEOIdPartner1']
                
                # Get other user's name and profile pic
                db_users = MongoDB.get_instance().get_collection('Users')
                other_user = db_users.find_one({"BLEOId": other_id}, {"userName": 1})
                
                if other_user:
                    conn['other_user'] = {
                        "bleoid": other_id,
                        "userName": other_user.get('userName', 'Unknown')
                    }
            
            return BLEOResponse.success(
                data={
                    "connections": connections,
                    "count": len(connections)
                },
                message="Connections retrieved successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve connections: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)