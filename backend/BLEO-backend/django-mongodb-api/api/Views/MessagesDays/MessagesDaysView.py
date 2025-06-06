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
from utils.validation_patterns import ValidationPatterns, ValidationRules
from rest_framework.exceptions import ValidationError

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
    Returns the linked partner's bleoid if valid, None otherwise.
    """
    try:
        # Get the Links collection
        db_links = MongoDB.get_instance().get_collection('Links')
        
        # Check for an accepted link where the user is either partner1 or partner2
        link = db_links.find_one({
            "$or": [
                {"bleoidPartner1": from_bleoid},
                {"bleoidPartner2": from_bleoid}
            ],
            "status": "accepted"
        })
        
        if not link:
            return None
        
        # Determine which partner is the linked user
        if link["bleoidPartner1"] == from_bleoid:
            return link["bleoidPartner2"]
        else:
            return link["bleoidPartner1"]
            
    except Exception as e:
        print(f"Error validating user link: {str(e)}")
        return None

def _find_partner_from_link(from_bleoid):
    """
    Find the partner's bleoid from an accepted link.
    Returns the partner's bleoid if found, None otherwise.
    """
    try:
        # Get the Links collection
        db_links = MongoDB.get_instance().get_collection('Links')
        
        # Find accepted link where user is either partner1 or partner2
        link = db_links.find_one({
            "$or": [
                {"bleoidPartner1": from_bleoid},
                {"bleoidPartner2": from_bleoid}
            ],
            "status": "accepted"
        })
        
        if not link:
            return None
        
        # Return the other partner's bleoid
        if link["bleoidPartner1"] == from_bleoid:
            return link["bleoidPartner2"]
        else:
            return link["bleoidPartner1"]
            
    except Exception as e:
        Logger.debug_error(
            f"Error finding partner from link for {from_bleoid}: {str(e)}",
            500,
            from_bleoid,
            ErrorSourceType.SERVER.value
        )
        return None

def _validate_link_between_users(from_bleoid, to_bleoid):
    """
    Validate that an accepted link exists between two users.
    Returns True if valid link exists, False otherwise.
    """
    try:
        db_links = MongoDB.get_instance().get_collection('Links')
        link = db_links.find_one({
            "$or": [
                {"bleoidPartner1": from_bleoid, "bleoidPartner2": to_bleoid},
                {"bleoidPartner1": to_bleoid, "bleoidPartner2": from_bleoid}
            ],
            "status": "accepted"
        })
        return link is not None
    except Exception:
        return False

class MessageDayListCreateView(APIView):
    """API view for listing and creating message days"""

    def get(self, request):
        """Get message days with optional filtering by from_bleoid, to_bleoid, date, or mood"""
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
            
            # Validate BLEOIDs if provided
            validated_from_bleoid = None
            validated_to_bleoid = None
            
            if from_bleoid:
                validated_from_bleoid = ValidationPatterns.validate_url_bleoid(from_bleoid, "fromBleoid")
            
            if to_bleoid:
                validated_to_bleoid = ValidationPatterns.validate_url_bleoid(to_bleoid, "toBleoid")
            
            # Build filter criteria using validated BLEOIDs
            filter_criteria = {}
            
            if validated_from_bleoid:
                filter_criteria['from_bleoid'] = validated_from_bleoid
                
            if validated_to_bleoid:
                filter_criteria['to_bleoid'] = validated_to_bleoid
            
            # Single date filtering
            if date:
                try:
                    date_obj = datetime.strptime(date, ValidationRules.STANDARD_DATE_FORMAT)
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
                    day['date'] = day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
                # Add quadrant information
                _add_quadrant_info(self, day)
            
            # Use serializer for consistent output
            serializer = MessagesDaysSerializer(message_days, many=True)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Messages days retrieved successfully"
            ).to_response()
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in query parameters - {str(e)}",
                400,
                None,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format in query parameters"
            ).to_response(status.HTTP_400_BAD_REQUEST)
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
            serializer = MessagesDaysSerializer(data=request.data)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"MessageDays creation validation failed: {serializer.errors}",
                    400,
                    request.data.get('from_bleoid'),
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Validation failed",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
        
            validated_data = serializer.validated_data
            from_bleoid = validated_data['from_bleoid']
        
            # STEP 1: Check if from_user exists FIRST
            db_users = MongoDB.get_instance().get_collection('Users')
            from_user = db_users.find_one({"bleoid": from_bleoid})
            
            if not from_user:
                Logger.debug_error(
                    f"User with bleoid {from_bleoid} not found",
                    404,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with bleoid {from_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)

            # STEP 2: Handle to_bleoid - either provided or auto-discover
            to_bleoid = validated_data.get('to_bleoid')
            if to_bleoid:
                # STEP 3: Check if provided to_bleoid user exists BEFORE checking link
                to_user = db_users.find_one({"bleoid": to_bleoid})
                if not to_user:
                    Logger.debug_error(
                        f"Partner with bleoid {to_bleoid} not found",
                        404,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"Partner with bleoid {to_bleoid} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # STEP 4: Now check if valid link exists between these existing users
                if not _validate_link_between_users(from_bleoid, to_bleoid):
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
                # STEP 5: Auto-discover to_bleoid from link
                to_bleoid = _find_partner_from_link(from_bleoid)
        
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
        
                # STEP 6: Check if discovered partner user exists
                to_user = db_users.find_one({"bleoid": to_bleoid})
                if not to_user:
                    Logger.debug_error(
                        f"Linked partner with bleoid {to_bleoid} not found in database",
                        404,
                        from_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"Linked partner with bleoid {to_bleoid} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
        
            # Continue with existing logic for date handling and creation...
            # Set default date if not provided
            if 'date' not in request.data:
                now = datetime.now()
                request.data['date'] = now.strftime(ValidationRules.STANDARD_DATE_FORMAT)

            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user and date
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "from_bleoid": from_bleoid,
                "to_bleoid": to_bleoid,
                "date": message_date
            })
            
            if existing_entry:
                Logger.debug_error(
                    f"Message day already exists for {from_bleoid} to {to_bleoid} on {message_date.strftime(ValidationRules.STANDARD_DATE_FORMAT)}",
                    409,
                    from_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for {from_bleoid} to {to_bleoid} on {message_date.strftime(ValidationRules.STANDARD_DATE_FORMAT)}"
                ).to_response(status.HTTP_409_CONFLICT)
        
            # Process messages - generate IDs
            messages = validated_data.get('messages', [])
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance
            message_day = MessagesDays(
                from_bleoid=from_bleoid,
                to_bleoid=to_bleoid,
                date=message_date,
                messages=processed_messages,
                mood=validated_data.get('mood'),
                energy_level=validated_data.get('energy_level'),
                pleasantness=validated_data.get('pleasantness')
            )
            
            # Save to MongoDB
            result = db_message_days.insert_one(message_day.to_dict())
            
            # Return created message day
            created_message_day = message_day.to_dict()
            created_message_day['_id'] = str(result.inserted_id)
            
            # Format date for response
            if 'date' in created_message_day and isinstance(created_message_day['date'], datetime):
                created_message_day['date'] = created_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
            
            # Add quadrant info
            _add_quadrant_info(self, created_message_day)
            
            # Use serializer for response
            response_serializer = MessagesDaysSerializer(created_message_day)
            
            # Log success
            Logger.debug_user_action(
                from_bleoid,
                f"Message day created successfully to {to_bleoid} with {len(processed_messages)} messages",
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
                f"Failed to create message day: {str(e)}",
                500,
                request.data.get('from_bleoid'),
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bleoid):
        """Delete all message days for a specific from_bleoid"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting all message days for user {bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"bleoid": validated_bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with bleoid {validated_bleoid} not found when deleting message days",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with bleoid {validated_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete all message days for this user
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_many({"from_bleoid": validated_bleoid})
            
            # Log no message days found
            if result.deleted_count == 0:
                Logger.debug_error(
                    f"No message days found for bleoid={validated_bleoid} during bulk delete",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message days found for from_bleoid={validated_bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                f"Successfully deleted {result.deleted_count} message day(s)",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={"deleted_count": result.deleted_count},
                message=f"Successfully deleted {result.deleted_count} message day(s) for from_bleoid={validated_bleoid}"
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
    """API view for creating message days with from_bleoid in URL path"""
    
    def post(self, request, bleoid):
        """Create a new message day with from_bleoid from URL path"""
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Add validated bleoid to request data
            data = request.data.copy()
            data['from_bleoid'] = validated_bleoid
            
            # Check if date is provided, if not initialize to today
            if 'date' not in data:
                now = datetime.now()
                data['date'] = now.strftime(ValidationRules.STANDARD_DATE_FORMAT)

            # STEP 1: Check if from_user exists FIRST
            db_users = MongoDB.get_instance().get_collection('Users')
            from_user = db_users.find_one({"bleoid": validated_bleoid})
            
            if not from_user:
                Logger.debug_error(
                    f"User with bleoid {validated_bleoid} not found",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with bleoid {validated_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)

            # STEP 2: Check if to_bleoid is provided and validate the user exists
            to_bleoid = None
            if 'to_bleoid' in data:
                to_bleoid = data['to_bleoid']
                
                # Check if to_user exists
                to_user = db_users.find_one({"bleoid": to_bleoid})
                if not to_user:
                    Logger.debug_error(
                        f"Partner with bleoid {to_bleoid} not found",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"Partner with bleoid {to_bleoid} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # STEP 3: Now check if a valid link exists between these users
                db_links = MongoDB.get_instance().get_collection('Links')
                link = db_links.find_one({
                    "$or": [
                        {"bleoidPartner1": validated_bleoid, "bleoidPartner2": to_bleoid},
                        {"bleoidPartner1": to_bleoid, "bleoidPartner2": validated_bleoid}
                    ],
                    "status": "accepted"
                })
                
                if not link:
                    Logger.debug_error(
                        f"No accepted link found between {validated_bleoid} and {to_bleoid}",
                        403,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError",
                        error_message=f"No accepted link found between {validated_bleoid} and {to_bleoid}"
                    ).to_response(status.HTTP_403_FORBIDDEN)
            else:
                # STEP 4: If to_bleoid is not provided, find the linked partner
                to_bleoid = _validate_user_link(validated_bleoid)
                
                if not to_bleoid:
                    Logger.debug_error(
                        f"User {validated_bleoid} is not linked with any partner",
                        403,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.error(
                        error_type="ValidationError", 
                        error_message=f"User {validated_bleoid} is not linked with any partner"
                    ).to_response(status.HTTP_403_FORBIDDEN)
                
                # STEP 5: Check if the discovered partner user exists
                to_user = db_users.find_one({"bleoid": to_bleoid})
                if not to_user:
                    Logger.debug_error(
                        f"Linked partner with bleoid {to_bleoid} not found in database",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"Linked partner with bleoid {to_bleoid} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Validate with serializer
            serializer = MessagesDaysSerializer(data=data)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"Invalid message day data: {serializer.errors}",
                    400,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
        
            # Get validated data
            validated_data = serializer.validated_data
            
            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user, partner, and date
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "from_bleoid": validated_bleoid,
                "to_bleoid": to_bleoid,
                "date": message_date
            })
            
            if existing_entry:
                Logger.debug_error(
                    f"Message day already exists for {validated_bleoid} to {to_bleoid} on {message_date.strftime(ValidationRules.STANDARD_DATE_FORMAT)}",
                    409,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for from_bleoid {validated_bleoid} to to_bleoid {to_bleoid} on {message_date.strftime(ValidationRules.STANDARD_DATE_FORMAT)}"
                ).to_response(status.HTTP_409_CONFLICT)
        
            # Process messages - generate IDs
            messages = validated_data.get('messages', [])
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance with midnight date
            message_day = MessagesDays(
                from_bleoid=validated_bleoid,  #  Use correct parameter names
                to_bleoid=to_bleoid,
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
                created_message_day['date'] = created_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
            
            # Add quadrant info
            _add_quadrant_info(self, created_message_day)
            
            # Use serializer for response
            response_serializer = MessagesDaysSerializer(created_message_day)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                f"Message day created successfully to {to_bleoid} with {len(processed_messages)} messages",
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
                f"Failed to create message day for {bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bleoid):
        """Delete all message days for a specific from_bleoid"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting all message days for user {bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"bleoid": validated_bleoid})
            
            if not user:
                Logger.debug_error(
                    f"User with bleoid {validated_bleoid} not found when deleting message days",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"User with bleoid {validated_bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete all message days for this user
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_many({"from_bleoid": validated_bleoid})
            
            # Log no message days found
            if result.deleted_count == 0:
                Logger.debug_error(
                    f"No message days found for bleoid={validated_bleoid} during bulk delete",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message days found for from_bleoid={validated_bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                f"Successfully deleted {result.deleted_count} message day(s)",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={"deleted_count": result.deleted_count},
                message=f"Successfully deleted {result.deleted_count} message day(s) for from_bleoid={validated_bleoid}"
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
        """Get message day by bleoid and date"""
        try:
            # No type conversion needed for bleoid anymore since it's a string
            date_obj = datetime.strptime(date, ValidationRules.STANDARD_DATE_FORMAT)
            
            # Midnight timestamp
            message_date = datetime(date_obj.year, date_obj.month, date_obj.day)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            return db.find_one({
                "from_bleoid": bleoid,
                "date": message_date
            })
        except ValueError:
            return None
    
    def get(self, request, bleoid=None, date=None):
        """Get message days by bleoid, date, or both"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Getting message day(s) - bleoid: {bleoid}, Date: {date}",
                LogType.INFO.value,
                200
            )
            
            if bleoid and date:
                # Single message day retrieval
                message_day = self.get_by_bleoid_and_date(bleoid, date)
                if not message_day:
                    Logger.debug_error(
                        f"No message day found for bleoid={bleoid} on date {date}",
                        404,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"No message day found for bleoid={bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Convert ObjectId to string
                message_day['_id'] = str(message_day['_id'])
                
                # Format date
                if 'date' in message_day and isinstance(message_day['date'], datetime):
                    message_day['date'] = message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
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
                # All message days for a specific bleoid
                db = MongoDB.get_instance().get_collection('MessagesDays')
                message_days = list(db.find({"from_bleoid": bleoid}))
                
                if not message_days:
                    Logger.debug_error(
                        f"No message days found for bleoid={bleoid}",
                        404,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    return BLEOResponse.not_found(
                        message=f"No message days found for bleoid={bleoid}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
            
            elif date:
                # All message days for a specific date
                try:
                    date_obj = datetime.strptime(date, ValidationRules.STANDARD_DATE_FORMAT)
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
                    message="bleoid or date is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Process message days for response
            for day in message_days:
                day['_id'] = str(day['_id'])
                if 'date' in day and isinstance(day['date'], datetime):
                    day['date'] = day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
                # Add quadrant information
                _add_quadrant_info(self, day)
            
            # Use serializer for consistent output
            serializer = MessagesDaysSerializer(message_days, many=True)
            
            # Log success
            Logger.debug_system_action(
                f"Retrieved {len(message_days)} message days" +
                (f" for bleoid={bleoid}" if bleoid else "") +
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
        """Update a message day by bleoid and date"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Updating message day for bleoid={bleoid} on date {date}",
                LogType.INFO.value,
                200
            )
            
            # Get existing message day
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                Logger.debug_error(
                    f"No message day found for bleoid={bleoid} on date {date} during update",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message day found for bleoid={bleoid} on date {date}"
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
            
            # Don't allow changing from_bleoid or date
            if 'from_bleoid' in validated_data:
                del validated_data['from_bleoid']
                
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
                    f"No changes made to message day for bleoid={bleoid} on date {date}",
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
                updated_message_day['date'] = updated_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
            
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
                f"Failed to update message day for bleoid={bleoid} on date {date}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to update message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date):
        """Delete a message day by bleoid and date"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting message day for bleoid={bleoid} on date {date}",
                LogType.INFO.value,
                200
            )
            
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                Logger.debug_error(
                    f"No message day found for bleoid={bleoid} on date {date} during deletion",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message=f"No message day found for bleoid={bleoid} on date {date}"
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
                f"Failed to delete message day for bleoid={bleoid} on date {date}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)