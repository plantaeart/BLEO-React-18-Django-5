from rest_framework.views import APIView
from rest_framework import status
from models.MessagesDays import MessagesDays
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime, timedelta
from models.response.BLEOResponse import BLEOResponse
from models.enums.MoodType import MoodType
from models.enums.MoodQuadrantType import MoodQuadrantType
from api.serializers import MessagesDaysSerializer
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

def _generate_message_ids(messages):
    """Generate IDs for messages that don't have them"""
    if not messages:
        return []
    
    processed_messages = []
    max_id = 0
    
    # Find the highest existing ID
    for msg in messages:
        if 'id' in msg and isinstance(msg['id'], int) and msg['id'] > max_id:
            max_id = msg['id']
    
    # Process each message
    for msg in messages:
        if 'id' not in msg or not isinstance(msg['id'], int):
            max_id += 1
            msg['id'] = max_id
        processed_messages.append(msg)
    
    return processed_messages

def _add_quadrant_info(self, message_day):
    """Helper method to add quadrant information to a message day"""
    if 'energy_level' in message_day and message_day['energy_level'] and \
        'pleasantness' in message_day and message_day['pleasantness']:
        try:
            energy = EnergyLevelType(message_day['energy_level'])
            pleasant = PleasantnessType(message_day['pleasantness'])
            quadrant = MoodQuadrantType.from_dimensions(energy, pleasant)
            message_day['quadrant'] = quadrant.value
        except (ValueError, AttributeError):
            message_day['quadrant'] = None

def _validate_user_link(from_bleoid):
    """
    Validate that the user is linked with someone.
    Returns the linked partner's BLEOId if valid, None otherwise.
    """
    try:
        # Get the Links collection
        db_links = MongoDB.get_instance().get_collection('Links')
        
        # Check for an accepted link where the user is either partner1 or partner2
        link = db_links.find_one({
            "$or": [
                {"BLEOIdPartner1": from_bleoid},
                {"BLEOIdPartner2": from_bleoid}
            ],
            "status": "accepted"
        })
        
        if not link:
            return None
        
        # Determine which partner is the linked user
        if link["BLEOIdPartner1"] == from_bleoid:
            return link["BLEOIdPartner2"]
        else:
            return link["BLEOIdPartner1"]
            
    except Exception as e:
        print(f"Error validating user link: {str(e)}")
        return None

class MessageDayListCreateView(APIView):
    """API view for listing and creating message days"""

    def get(self, request):
        """Get message days with optional filtering by fromBLEOId, toBLEOId, date, or mood"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Getting message days with filters: {request.query_params}",
                LogType.INFO.value,
                200
            )
            
            # Get query parameters
            from_bleoid = request.query_params.get('fromBleoid')
            to_bleoid = request.query_params.get('toBleoid')
            date = request.query_params.get('date')
            mood = request.query_params.get('mood')
            energy_level = request.query_params.get('energy_level')
            pleasantness = request.query_params.get('pleasantness')
            
            # Build filter criteria
            filter_criteria = {}
            
            if from_bleoid:
                filter_criteria['fromBLEOId'] = from_bleoid
                
            if to_bleoid:
                filter_criteria['toBLEOId'] = to_bleoid
            
            # Single date filtering
            if date:
                try:
                    date_obj = datetime.strptime(date, '%d-%m-%Y')
                    start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day)
                    end_of_day = start_of_day + timedelta(days=1, microseconds=-1)
                    
                    filter_criteria['date'] = {
                        "$gte": start_of_day,
                        "$lte": end_of_day
                    }
                except ValueError:
                    return BLEOResponse.validation_error(
                        message="Invalid date format, use DD-MM-YYYY"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
        
            # Mood filtering
            if mood:
                filter_criteria['mood'] = mood
            
            # Energy level filtering
            if energy_level:
                filter_criteria['energy_level'] = energy_level
                
            # PleasantnessType filtering
            if pleasantness:
                filter_criteria['pleasantness'] = pleasantness
            
            # Query database
            db = MongoDB.get_instance().get_collection('MessagesDays')
            message_days = list(db.find(filter_criteria))
            
            # Log success
            Logger.debug_system_action(
                f"Retrieved {len(message_days)} message days" + 
                (f" for user {from_bleoid}" if from_bleoid else "") +
                (f" to user {to_bleoid}" if to_bleoid else "") +
                (f" on date {date}" if date else ""),
                LogType.SUCCESS.value,
                200
            )
            
            # Convert ObjectId to string for JSON serialization
            for day in message_days:
                day['_id'] = str(day['_id'])
                if 'date' in day and isinstance(day['date'], datetime):
                    day['date'] = day['date'].strftime('%d-%m-%Y')
                
                # Add quadrant information
                _add_quadrant_info(self, day)
            
            # Use serializer for consistent output
            serializer = MessagesDaysSerializer(message_days, many=True)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Messages days retrieved successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve message days: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve message days: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new message day"""
        try:
            # Get fromBLEOId from request data or query params
            from_bleoid = request.data.get('fromBLEOId') or request.query_params.get('fromBleoid')
            
            # Log request
            Logger.debug_system_action(
                f"Creating new message day for user {from_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Check if date is provided in request data if not initialize to today
            if 'date' not in request.data:
                now = datetime.now()
                request.data['date'] = now.strftime('%d-%m-%Y')
        
            # Ensure fromBLEOId is provided in request data
            if 'fromBLEOId' not in request.data:
                from_bleoid = request.query_params.get('fromBleoid')
                if not from_bleoid:
                    return BLEOResponse.validation_error(
                        message="fromBLEOId is required"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                request.data['fromBLEOId'] = from_bleoid

            # Validate with serializer
            serializer = MessagesDaysSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                # If validation fails, log error
                Logger.debug_error(
                    f"Invalid message day data: {serializer.errors}",
                    400,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            from_bleoid = validated_data.get('fromBLEOId')
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": from_bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with BLEOId {from_bleoid} not found when creating message day",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {from_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # NEW: Check if user is linked with someone
            to_bleoid = None
            if 'toBLEOId' in validated_data:
                # If toBLEOId is provided, validate it's actually linked to this user
                to_bleoid = validated_data.get('toBLEOId')
                
                # Check if a valid link exists between these users
                db_links = MongoDB.get_instance().get_collection('Links')
                link = db_links.find_one({
                    "$or": [
                        {"BLEOIdPartner1": from_bleoid, "BLEOIdPartner2": to_bleoid},
                        {"BLEOIdPartner1": to_bleoid, "BLEOIdPartner2": from_bleoid}
                    ],
                    "status": "accepted"
                })
                
                if not link:
                    Logger.debug_error(
                        f"No accepted link found between {from_bleoid} and {to_bleoid}",
                        403,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError",
                        error_message=f"No accepted link found between {from_bleoid} and {to_bleoid}"
                    ).to_response(status.HTTP_403_FORBIDDEN)
            else:
                # If toBLEOId is not provided, find the linked partner
                to_bleoid = _validate_user_link(from_bleoid)
                
                if not to_bleoid:
                    Logger.debug_error(
                        f"User {from_bleoid} is not linked with any partner",
                        403,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError", 
                        error_message=f"User {from_bleoid} is not linked with any partner"
                    ).to_response(status.HTTP_403_FORBIDDEN)
            
            # Add the toBLEOId to validated data
            validated_data['toBLEOId'] = to_bleoid
        
            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user and date using exact date match
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "fromBLEOId": from_bleoid,
                "toBLEOId": to_bleoid,
                "date": message_date
            })
            
            if existing_entry:
                Logger.debug_error(
                    f"Message day already exists for {from_bleoid} to {to_bleoid} on {message_date.strftime('%d-%m-%Y')}",
                    409,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for fromBLEOId {from_bleoid} to toBLEOId {to_bleoid} on {message_date.strftime('%d-%m-%Y')}"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Process messages - generate IDs
            messages = validated_data.get('messages', [])
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance with midnight date
            message_day = MessagesDays(
                fromBLEOId=from_bleoid,
                toBLEOId=to_bleoid,
                date=message_date,
                messages=processed_messages,
                mood=validated_data.get('mood'),
                energy_level=validated_data.get('energy_level'),
                pleasantness=validated_data.get('pleasantness')
            )
            
            # Save to MongoDB
            result = db_message_days.insert_one(message_day.to_dict())
            
            # Return created message day with ID
            created_message_day = message_day.to_dict()
            created_message_day['_id'] = str(result.inserted_id)
            
            # Format date for response
            if 'date' in created_message_day and isinstance(created_message_day['date'], datetime):
                created_message_day['date'] = created_message_day['date'].strftime('%d-%m-%Y')
            
            # Add quadrant info
            _add_quadrant_info(self, created_message_day)
            
            # Use serializer for response
            response_serializer = MessagesDaysSerializer(created_message_day)
            
            # Log success (without logging message content)
            Logger.debug_user_action(
                from_bleoid,
                f"Message day created successfully with {len(processed_messages)} messages",
                LogType.SUCCESS.value,
                201
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to create message day for {from_bleoid}: {str(e)}",
                500,
                from_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bleoid):
        """Delete all message days for a specific fromBLEOId"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting all message days for user {bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with BLEOId {bleoid} not found when deleting message days",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete all message days for this user
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_many({"fromBLEOId": bleoid})
            
            # Log no message days found
            if result.deleted_count == 0:
                Logger.debug_error(
                    f"No message days found for BLEOId={bleoid} during bulk delete",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message days found for fromBLEOId={bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Successfully deleted {result.deleted_count} message day(s)",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={"deleted_count": result.deleted_count},
                message=f"Successfully deleted {result.deleted_count} message day(s) for fromBLEOId={bleoid}"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to delete message days for {bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete message days: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class MoodOptionsView(APIView):
    """API view for getting mood-related options"""
    
    def get(self, request):
        """Get energy levels, PleasantnessType options, and filtered moods"""
        try:
            # Log request
            Logger.debug_system_action(
                "Getting mood options",
                LogType.INFO.value,
                200
            )
            
            # Get query parameters for filtering
            energy = request.query_params.get('energy')
            pleasantness = request.query_params.get('pleasantness')
            
            # Create response with all options
            response_data = {
                "energy_levels": [{"value": level.value, "label": level.value.capitalize()} 
                                 for level in EnergyLevelType],
                "pleasantness_options": [{"value": option.value, "label": option.value.capitalize()} 
                                        for option in PleasantnessType],
                "mood_quadrants": [{"value": quadrant.value, 
                                   "label": quadrant.value.capitalize()} 
                                   for quadrant in MoodQuadrantType],
            }
            
            # Filter moods by quadrant if energy and PleasantnessType are provided
            if energy and PleasantnessType:
                try:
                    energy_enum = EnergyLevelType(energy)
                    pleasantness_enum = PleasantnessType(PleasantnessType)
                    quadrant = MoodQuadrantType.from_dimensions(energy_enum, pleasantness_enum)
                    
                    # Get moods for this quadrant
                    matching_moods = [mood for mood in MoodType 
                                     if mood.quadrant == quadrant]
                    
                    response_data["filtered_moods"] = [
                        {"value": mood.value, "label": mood.value}
                        for mood in matching_moods
                    ]
                    response_data["selected_quadrant"] = quadrant.value
                except ValueError:
                    # Invalid energy or PleasantnessType value
                    response_data["filtered_moods"] = []
                    response_data["error"] = "Invalid energy or PleasantnessType value"
            else:
                # No filtering, return all moods
                response_data["all_moods"] = [
                    {"value": mood.value, "label": mood.value}
                    for mood in MoodType
                ]
            
            # Log filter application if applicable
            if energy and pleasantness:
                Logger.debug_system_action(
                    f"Filtering moods by energy={energy} and pleasantness={pleasantness}",
                    LogType.INFO.value,
                    200
                )
            
            # Log success
            Logger.debug_system_action(
                "Mood options retrieved successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=response_data,
                message="Mood options retrieved successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve mood options: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve mood options: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageDayCreateView(APIView):
    """API view for creating message days with fromBLEOId in URL path"""
    
    def post(self, request, bleoid):
        """Create a new message day with fromBLEOId from URL path"""
        try:
            # Log request
            Logger.debug_user_action(
                bleoid,
                "Creating new message day via path parameter",
                LogType.INFO.value,
                200
            )
            
            data = request.data.copy()

            # Add fromBLEOId from URL to data
            data['fromBLEOId'] = bleoid
            
            # Check if date is provided, if not initialize to today
            if 'date' not in data:
                now = datetime.now()
                data['date'] = now.strftime('%d-%m-%Y')

            # NEW: Check if user is linked with someone
            to_bleoid = None
            if 'toBLEOId' in data:
                # If toBLEOId is provided, validate it's actually linked to this user
                to_bleoid = data['toBLEOId']
                
                # Check if a valid link exists between these users
                db_links = MongoDB.get_instance().get_collection('Links')
                link = db_links.find_one({
                    "$or": [
                        {"BLEOIdPartner1": bleoid, "BLEOIdPartner2": to_bleoid},
                        {"BLEOIdPartner1": to_bleoid, "BLEOIdPartner2": bleoid}
                    ],
                    "status": "accepted"
                })
                
                if not link:
                    Logger.debug_error(
                        f"No accepted link found between {bleoid} and {to_bleoid}",
                        403,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError",
                        error_message=f"No accepted link found between {bleoid} and {to_bleoid}"
                    ).to_response(status.HTTP_403_FORBIDDEN)
            else:
                # If toBLEOId is not provided, find the linked partner
                to_bleoid = _validate_user_link(bleoid)
                
                if not to_bleoid:
                    Logger.debug_error(
                        f"User {bleoid} is not linked with any partner",
                        403,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError", 
                        error_message=f"User {bleoid} is not linked with any partner"
                    ).to_response(status.HTTP_403_FORBIDDEN)
                
                # Add the toBLEOId to the data
                data['toBLEOId'] = to_bleoid

            # Validate with serializer
            serializer = MessagesDaysSerializer(data=data)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"Invalid message day data: {serializer.errors}",
                    400,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get validated data
            validated_data = serializer.validated_data
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with BLEOId {bleoid} not found when creating message day",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Check if partner exists
            partner = db_users.find_one({"BLEOId": to_bleoid})
            if not partner:
                return BLEOResponse.not_found(
                    message=f"Partner with BLEOId {to_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user, partner, and date
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "fromBLEOId": bleoid,
                "toBLEOId": to_bleoid,
                "date": message_date
            })
            
            if existing_entry:
                Logger.debug_error(
                    f"Message day already exists for {bleoid} to {to_bleoid} on {message_date.strftime('%d-%m-%Y')}",
                    409,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for fromBLEOId {bleoid} to toBLEOId {to_bleoid} on {message_date.strftime('%d-%m-%Y')}"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Process messages - generate IDs
            messages = validated_data.get('messages', [])
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance with midnight date
            message_day = MessagesDays(
                fromBLEOId=bleoid,
                toBLEOId=to_bleoid,
                date=message_date,
                messages=processed_messages,
                mood=validated_data.get('mood'),
                energy_level=validated_data.get('energy_level'),
                pleasantness=validated_data.get('pleasantness')
            )
            
            # Save to MongoDB
            result = db_message_days.insert_one(message_day.to_dict())
            
            # Return created message day with ID
            created_message_day = message_day.to_dict()
            created_message_day['_id'] = str(result.inserted_id)
            
            # Format date for response
            if 'date' in created_message_day and isinstance(created_message_day['date'], datetime):
                created_message_day['date'] = created_message_day['date'].strftime('%d-%m-%Y')
            
            # Add quadrant info
            _add_quadrant_info(self, created_message_day)
            
            # Use serializer for response
            response_serializer = MessagesDaysSerializer(created_message_day)
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to create message day for {bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bleoid):
        """Delete all message days for a specific fromBLEOId"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting all message days for user {bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with BLEOId {bleoid} not found when deleting message days",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete all message days for this user
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_many({"fromBLEOId": bleoid})
            
            # Log no message days found
            if result.deleted_count == 0:
                Logger.debug_error(
                    f"No message days found for BLEOId={bleoid} during bulk delete",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message days found for fromBLEOId={bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Successfully deleted {result.deleted_count} message day(s)",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={"deleted_count": result.deleted_count},
                message=f"Successfully deleted {result.deleted_count} message day(s) for fromBLEOId={bleoid}"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to delete message days for {bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete message days: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class MessageDayDetailView(APIView):
    """API view for getting, updating and deleting a message day by bleoid and date"""
    
    def get_by_bleoid_and_date(self, bleoid, date):
        """Get message day by BLEOId and date"""
        try:
            # No type conversion needed for bleoid anymore since it's a string
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            
            # Midnight timestamp
            message_date = datetime(date_obj.year, date_obj.month, date_obj.day)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            return db.find_one({
                "fromBLEOId": bleoid,
                "date": message_date
            })
        except ValueError:
            return None
    
    def get(self, request, bleoid=None, date=None):
        """Get message days by BLEOId, date, or both"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Getting message day(s) - BLEOId: {bleoid}, Date: {date}",
                LogType.INFO.value,
                200
            )
            
            if bleoid and date:
                # Single message day retrieval
                message_day = self.get_by_bleoid_and_date(bleoid, date)
                if not message_day:
                    Logger.debug_error(
                        f"No message day found for BLEOId={bleoid} on date {date}",
                        404,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"No message day found for BLEOId={bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Convert ObjectId to string
                message_day['_id'] = str(message_day['_id'])
                
                # Format date
                if 'date' in message_day and isinstance(message_day['date'], datetime):
                    message_day['date'] = message_day['date'].strftime('%d-%m-%Y')
                
                # Add quadrant information
                _add_quadrant_info(self, message_day)
                
                # Use serializer for consistent output
                serializer = MessagesDaysSerializer(message_day)
                
                # Log success
                Logger.debug_user_action(
                    bleoid,
                    f"Retrieved message day for date {date}",
                    LogType.SUCCESS.value,
                    200
                )
                
                return BLEOResponse.success(
                    data=serializer.data,
                    message="Messages days retrieved successfully"
                ).to_response()
            
            elif bleoid:
                # All message days for a specific BLEOId
                db = MongoDB.get_instance().get_collection('MessagesDays')
                message_days = list(db.find({"fromBLEOId": bleoid}))
                
                if not message_days:
                    Logger.debug_error(
                        f"No message days found for BLEOId={bleoid}",
                        404,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"No message days found for BLEOId={bleoid}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
            
            elif date:
                # All message days for a specific date
                try:
                    date_obj = datetime.strptime(date, '%d-%m-%Y')
                    start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day)
                    end_of_day = start_of_day + timedelta(days=1, microseconds=-1)
                    
                    db = MongoDB.get_instance().get_collection('MessagesDays')
                    message_days = list(db.find({
                        "date": {
                            "$gte": start_of_day,
                            "$lte": end_of_day
                        }
                    }))
                    
                    if not message_days:
                        Logger.debug_error(
                            f"No message days found for date {date}",
                            404,
                            None,
                            ErrorSourceType.SERVER.value
                        )
                        return BLEOResponse.not_found(
                            message=f"No message days found for date {date}"
                        ).to_response(status.HTTP_404_NOT_FOUND)
                    
                except ValueError:
                    Logger.debug_error(
                        f"Invalid date format: {date}",
                        400,
                        None,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.validation_error(
                        message="Invalid date format, use DD-MM-YYYY"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            else:
                # No filters provided
                Logger.debug_error(
                    "No bleoid or date provided for message day retrieval",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="BLEOId or date is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Process message days for response
            for day in message_days:
                day['_id'] = str(day['_id'])
                if 'date' in day and isinstance(day['date'], datetime):
                    day['date'] = day['date'].strftime('%d-%m-%Y')
                
                # Add quadrant information
                _add_quadrant_info(self, day)
            
            # Use serializer for consistent output
            serializer = MessagesDaysSerializer(message_days, many=True)
            
            # Log success
            Logger.debug_system_action(
                f"Retrieved {len(message_days)} message days" +
                (f" for BLEOId={bleoid}" if bleoid else "") +
                (f" on date {date}" if date else ""),
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Messages days retrieved successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve message day(s): {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve message day(s): {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, bleoid, date):
        """Update a message day by BLEOId and date"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Updating message day for BLEOId={bleoid} on date {date}",
                LogType.INFO.value,
                200
            )
            
            # Get existing message day
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                Logger.debug_error(
                    f"No message day found for BLEOId={bleoid} on date {date} during update",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get request data
            data = request.data
            
            # Use serializer for validation
            serializer = MessagesDaysSerializer(data=data, partial=True)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"Invalid message day update data: {serializer.errors}",
                    400,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            validated_data = serializer.validated_data
            
            # Don't allow changing fromBLEOId or date
            if 'fromBLEOId' in validated_data:
                del validated_data['fromBLEOId']
                
            if 'date' in validated_data:
                del validated_data['date']
            
            # Process messages if provided
            if 'messages' in validated_data:
                validated_data['messages'] = _generate_message_ids(validated_data['messages'])
            
            # Update in database
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.update_one(
                {"_id": message_day['_id']},
                {"$set": validated_data}
            )
            
            if result.modified_count == 0:
                Logger.debug_system_action(
                    f"No changes made to message day for BLEOId={bleoid} on date {date}",
                    LogType.INFO.value,
                    200
                )
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get updated message day
            updated_message_day = self.get_by_bleoid_and_date(bleoid, date)
            updated_message_day['_id'] = str(updated_message_day['_id'])
            
            # Format date for response
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
            
            # Add quadrant information
            _add_quadrant_info(self, updated_message_day)
            
            # Use serializer for response
            response_serializer = MessagesDaysSerializer(updated_message_day)
            
            # Log success (without logging message content)
            message_count = len(updated_message_day.get('messages', []))
            Logger.debug_user_action(
                bleoid,
                f"Updated message day on date {date} with {message_count} messages",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day updated successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to update message day for BLEOId={bleoid} on date {date}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to update message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date):
        """Delete a message day by BLEOId and date"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting message day for BLEOId={bleoid} on date {date}",
                LogType.INFO.value,
                200
            )
            
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                Logger.debug_error(
                    f"No message day found for BLEOId={bleoid} on date {date} during deletion",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete from database
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_one({"_id": message_day['_id']})
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Message day deleted for date {date}",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                message="Message day deleted successfully"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to delete message day for BLEOId={bleoid} on date {date}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)