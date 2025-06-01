from rest_framework.views import APIView
from rest_framework import status
from models.response.BLEOResponse import BLEOResponse
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime
from api.serializers import ConnectionRequestSerializer, ConnectionSerializer, ConnectionResponseSerializer, UserSerializer, ConnectionFilterSerializer
from models.enums.ConnectionStatusType import ConnectionStatusType
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class ConnectionRequestView(APIView):
    """API view for sending connection requests"""
    
    def post(self, request):
        """Send a connection request"""
        try:
            # Get IDs for logging
            from_bleoid = request.data.get('from_bleoid')
            to_bleoid = request.data.get('to_bleoid')

            # Log request
            Logger.debug_user_action(
                from_bleoid,
                f"Sending connection request to user {to_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Validate request data using serializer
            serializer = ConnectionRequestSerializer(data=request.data)
            if not serializer.is_valid():
                # Log validation error
                Logger.debug_error(
                    f"Invalid connection request data: {serializer.errors}",
                    400,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            from_bleoid = validated_data['from_bleoid']
            to_bleoid = validated_data['to_bleoid']
            
            # Check users exist
            db_users = MongoDB.get_instance().get_collection('Users')
            from_user = db_users.find_one({"BLEOId": from_bleoid})
            to_user = db_users.find_one({"BLEOId": to_bleoid})
            
            if not from_user or not to_user:
                # Log user not found error
                Logger.debug_error(
                    f"One or both users not found: from={from_bleoid}, to={to_bleoid}",
                    404,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message="One or both users not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db_links = MongoDB.get_instance().get_collection('Links')
            
            # Check if sender already has an active connection or pending request
            existing_from = db_links.find_one({
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": {"$ne": None},
                "status": {"$in": [ConnectionStatusType.PENDING, ConnectionStatusType.ACCEPTED]}
            })
            
            if existing_from:
                if existing_from["BLEOIdPartner2"] == to_bleoid:
                    # Log duplicate connection error
                    Logger.debug_error(
                        f"User {from_bleoid} already has a connection request with {to_bleoid}",
                        400,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.error(
                        error_type="DuplicateError",
                        error_message="You already have a connection request with this user"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                else:
                    # Log connection limit error
                    Logger.debug_error(
                        f"User {from_bleoid} already has an active connection with {existing_from['BLEOIdPartner2']}",
                        400,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.error(
                        error_type="LimitExceeded",
                        error_message="You already have an active connection or pending request with someone else"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check if receiver already has an active connection
            existing_to = db_links.find_one({
                "$or": [
                    {"BLEOIdPartner1": to_bleoid, "status": ConnectionStatusType.ACCEPTED},
                    {"BLEOIdPartner2": to_bleoid, "status": ConnectionStatusType.ACCEPTED}
                ]
            })
            
            if existing_to:
                # Log connection limit error for receiver
                other_user = existing_to["BLEOIdPartner1"] if existing_to["BLEOIdPartner2"] == to_bleoid else existing_to["BLEOIdPartner2"]
                Logger.debug_error(
                    f"User {to_bleoid} already has an active connection with {other_user}",
                    400,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.error(
                    error_type="LimitExceeded",
                    error_message="The user you're trying to connect with already has an active connection"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check for existing rejected/blocked requests - allow overwrite
            existing_rejected = db_links.find_one({
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": to_bleoid,
                "status": {"$in": [ConnectionStatusType.REJECTED, ConnectionStatusType.BLOCKED]}
            })
            
            if existing_rejected:
                # Log renewing request
                Logger.debug_user_action(
                    from_bleoid,
                    f"Renewing previously {existing_rejected['status']} connection request with {to_bleoid}",
                    LogType.INFO.value,
                    200
                )
                
                # Update existing rejected connection to pending
                result = db_links.update_one(
                    {"_id": existing_rejected["_id"]},
                    {
                        "$set": {
                            "status": ConnectionStatusType.PENDING,
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                updated = db_links.find_one({"_id": existing_rejected["_id"]})
                updated["_id"] = str(updated["_id"])

                # Use the serializer for consistent output
                response_serializer = ConnectionSerializer(updated)

                # Log success
                Logger.debug_user_action(
                    from_bleoid,
                    f"Connection request to {to_bleoid} renewed successfully",
                    LogType.SUCCESS.value,
                    200
                )
                
                return BLEOResponse.success(
                    data=response_serializer.data,
                    message="Connection request renewed"
                ).to_response(status.HTTP_200_OK)
            
            # Create connection request
            link = {
                "BLEOIdPartner1": from_bleoid,
                "BLEOIdPartner2": to_bleoid,
                "status": ConnectionStatusType.PENDING,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result = db_links.insert_one(link)
            
            # Get created link with ID
            created_link = link
            created_link["_id"] = str(result.inserted_id)
            
            # Serialize response
            response_serializer = ConnectionSerializer(created_link)
            
            # Log success
            Logger.debug_user_action(
                from_bleoid,
                f"Connection request to {to_bleoid} sent successfully",
                LogType.SUCCESS.value,
                201
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Connection request sent"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            # Get from_bleoid for logging if available
            from_bleoid = None
            try:
                from_bleoid = request.data.get('from_bleoid')
            except:
                pass
                
            # Log error
            Logger.debug_error(
                f"Failed to send connection request: {str(e)}",
                500,
                from_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to send connection request: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConnectionResponseView(APIView):
    """API view for responding to connection requests"""
    
    def put(self, request, connection_id):
        """Accept/Reject connection request"""
        try:
            # Log request
            action = request.data.get('action')
            
            # Log request
            Logger.debug_system_action(
                f"Processing connection response for connection_id={connection_id}, action={action}",
                LogType.INFO.value,
                200
            )
            
            # Validate action using serializer
            serializer = ConnectionResponseSerializer(data=request.data)
            if not serializer.is_valid():
                # Log validation error
                Logger.debug_error(
                    f"Invalid connection response data: {serializer.errors}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            action = serializer.validated_data['action']
            
            # Get connection
            db_links = MongoDB.get_instance().get_collection('Links')
            connection = db_links.find_one({"_id": ObjectId(connection_id)})
            
            if not connection:
                # Log not found error
                Logger.debug_error(
                    f"Connection request with ID {connection_id} not found",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message="Connection request not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Extract user IDs for logging
            from_bleoid = connection.get('BLEOIdPartner1')
            to_bleoid = connection.get('BLEOIdPartner2')
                
            # If accepting, check if receiver already has an active connection
            if action == 'accept':
                # Log acceptance check
                Logger.debug_user_action(
                    to_bleoid,
                    f"Checking if user can accept connection from {from_bleoid}",
                    LogType.INFO.value,
                    200
                )
                
                # Check if receiver already has an active connection
                existing_to = db_links.find_one({
                    "$and": [
                        {"_id": {"$ne": ObjectId(connection_id)}},  # Exclude current connection
                        {"$or": [
                            {"BLEOIdPartner1": to_bleoid, "status": ConnectionStatusType.ACCEPTED},
                            {"BLEOIdPartner2": to_bleoid, "status": ConnectionStatusType.ACCEPTED}
                        ]}
                    ]
                })
                
                if existing_to:
                    # Log limit error
                    other_user = existing_to.get('BLEOIdPartner1') if existing_to.get('BLEOIdPartner2') == to_bleoid else existing_to.get('BLEOIdPartner2')
                    Logger.debug_error(
                        f"User {to_bleoid} already has an active connection with {other_user}",
                        400,
                        to_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.error(
                        error_type="LimitExceeded",
                        error_message="You already have an active connection with someone else"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Map action to status
            status_map = {
                'accept': ConnectionStatusType.ACCEPTED,
                'reject': ConnectionStatusType.REJECTED,
                'block': ConnectionStatusType.BLOCKED
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
                # Log no changes
                Logger.debug_error(
                    f"No changes made to connection {connection_id} with action {action}",
                    400,
                    to_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.error(
                    error_type="UpdateError",
                    error_message="No changes made"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get updated connection
            updated_connection = db_links.find_one({"_id": ObjectId(connection_id)})
            updated_connection['_id'] = str(updated_connection['_id'])
            
            # Serialize response
            response_serializer = ConnectionSerializer(updated_connection)
            
            # Log success
            Logger.debug_user_action(
                to_bleoid,
                f"Connection with {from_bleoid} updated to {status_map[action]} successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message=f"Connection request {action}ed"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to process connection response for ID {connection_id}: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to process connection response: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConnectionListView(APIView):
    """API view for listing user connections"""
    
    def get(self, request):
        """Get all connections for a user"""
        try:
            # Get bleoid for logging
            bleoid = request.query_params.get('bleoid')
            
            # Log request
            Logger.debug_user_action(
                bleoid,
                "Retrieving connections list",
                LogType.INFO.value,
                200
            )
            
            # Validate query parameters
            filter_serializer = ConnectionFilterSerializer(data=request.query_params)
            if not filter_serializer.is_valid():
                # Log validation error
                Logger.debug_error(
                    f"Invalid connection filter parameters: {filter_serializer.errors}",
                    400,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid filter parameters",
                    errors=filter_serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)

            validated_filters = filter_serializer.validated_data
            bleoid = validated_filters['bleoid']
            status_filter = validated_filters.get('status')
            direction = validated_filters.get('direction', 'both')
            
            # Build query based on direction
            if direction == 'outgoing':
                query = {"BLEOIdPartner1": bleoid}
            elif direction == 'incoming':
                query = {"BLEOIdPartner2": bleoid}
            else: # both
                query = {"$or": [{"BLEOIdPartner1": bleoid}, {"BLEOIdPartner2": bleoid}]}
            
            # Add status filter if not 'all'
            if status_filter and status_filter != 'all':
                query["status"] = status_filter
            
            # Log filter details
            Logger.debug_user_action(
                bleoid,
                f"Filtering connections with: direction={direction}, status={status_filter or 'all'}",
                LogType.INFO.value,
                200
            )
            
            # Get connections
            db_links = MongoDB.get_instance().get_collection('Links')
            connections = list(db_links.find(query))
            
            # Enrich connections with user info
            for conn in connections:
                conn['_id'] = str(conn['_id'])
                
                # Add user info for the other party in each connection
                other_id = conn['BLEOIdPartner2'] if conn['BLEOIdPartner1'] == bleoid else conn['BLEOIdPartner1']
                
                # Get other user's name and profile pic
                db_users = MongoDB.get_instance().get_collection('Users')
                other_user = db_users.find_one({"BLEOId": other_id}, {"userName": 1, "profilePic": 1, "email": 1})
                
                if other_user:
                    other_user['_id'] = str(other_user.get('_id', ''))
                    # Get profile picture in proper format
                    user_serializer = UserSerializer(other_user)
                    conn['other_user'] = {
                        "bleoid": other_id,
                        "userName": other_user.get('userName', 'Unknown'),
                        "profilePic": user_serializer.data.get('profilePic')
                    }
            
            # Use serializer for response with context
            serializer = ConnectionSerializer(
                connections, 
                many=True,
                context={'current_user': bleoid}
            )
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Retrieved {len(connections)} connections successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={
                    "connections": serializer.data,
                    "count": len(connections)
                },
                message="Connections retrieved successfully"
            ).to_response()
            
        except Exception as e:
            # Get bleoid for logging if available
            bleoid = None
            try:
                bleoid = request.query_params.get('bleoid')
            except:
                pass
                
            # Log error
            Logger.debug_error(
                f"Failed to retrieve connections: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve connections: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)