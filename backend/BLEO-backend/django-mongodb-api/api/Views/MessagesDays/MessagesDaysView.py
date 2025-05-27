from rest_framework.views import APIView
from rest_framework import status
from models.MessagesDays import MessagesDays
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime, timedelta
from models.response.BLEOResponse import BLEOResponse
from models.enums.MoodType import MoodType
from models.enums.EnergyPleasantnessType import EnergyLevel, Pleasantness, MoodQuadrant
from api.serializers import MessagesDayserializer

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
            energy = EnergyLevel(message_day['energy_level'])
            pleasant = Pleasantness(message_day['pleasantness'])
            quadrant = MoodQuadrant.from_dimensions(energy, pleasant)
            message_day['quadrant'] = quadrant.value
        except (ValueError, AttributeError):
            message_day['quadrant'] = None

class MessageDayListCreateView(APIView):
    """API view for listing and creating message days"""


    def get(self, request):
        """Get message days with optional filtering by BLEOId, date, or mood"""
        try:
            # Get query parameters
            bleoid = request.query_params.get('bleoid')
            date = request.query_params.get('date')
            mood = request.query_params.get('mood')
            energy_level = request.query_params.get('energy_level')
            pleasantness = request.query_params.get('pleasantness')
            
            # Build filter criteria
            filter_criteria = {}
            
            if bleoid:
                try:
                    filter_criteria['BLEOId'] = bleoid
                except ValueError:
                    return BLEOResponse.validation_error(
                        message="Invalid BLEOId format, must be a number"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
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
                
            # Pleasantness filtering
            if pleasantness:
                filter_criteria['pleasantness'] = pleasantness
            
            # Query database
            db = MongoDB.get_instance().get_collection('MessagesDays')
            message_days = list(db.find(filter_criteria))
            
            # Convert ObjectId to string for JSON serialization
            for day in message_days:
                day['_id'] = str(day['_id'])
                if 'date' in day and isinstance(day['date'], datetime):
                    day['date'] = day['date'].strftime('%d-%m-%Y')
                
                # Add quadrant information
                _add_quadrant_info(self, day)
            
            # Use serializer for consistent output
            serializer = MessagesDayserializer(message_days, many=True)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Message days retrieved successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve message days: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new message day"""
        try:
            # Check if date is provided in request data if not initialize to today
            if 'date' not in request.data:
                now = datetime.now()
                request.data['date'] = now.strftime('%d-%m-%Y')
            
            # Ensure BLEOId is provided in request data if not get it from URL
            if 'BLEOId' not in request.data:
                bleoid = request.query_params.get('bleoid')
                if not bleoid:
                    return BLEOResponse.validation_error(
                        message="BLEOId is required"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                request.data['BLEOId'] = bleoid

            # Validate with serializer
            serializer = MessagesDayserializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            validated_data = serializer.validated_data
            bleoid = validated_data['BLEOId']
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user and date using exact date match
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "BLEOId": bleoid,
                "date": message_date
            })
            
            if existing_entry:
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for BLEOId {bleoid} on {message_date.strftime('%d-%m-%Y')}"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Process messages - generate IDs
            messages = validated_data.get('messages', [])  # Use validated_data instead
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance with midnight date
            message_day = MessagesDays(
                BLEOId=bleoid,
                date=message_date,
                messages=processed_messages,
                mood=validated_data.get('mood'),  # Use validated_data instead
                energy_level=validated_data.get('energy_level'),  # Use validated_data instead
                pleasantness=validated_data.get('pleasantness')  # Use validated_data instead
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
            response_serializer = MessagesDayserializer(created_message_day)
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageDayDetailView(APIView):
    """API view for getting, updating and deleting a message day by bleoid and date"""
    
    def get_by_bleoid_and_date(self, bleoid, date):
        """Get a message day by BLEOId and date"""
        try:
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            
            # Define start and end of the day
            start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day)
            end_of_day = start_of_day + timedelta(days=1, microseconds=-1)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            return db.find_one({
                "BLEOId": bleoid,  
                "date": {"$gte": start_of_day, "$lte": end_of_day}
            })
        except ValueError:  # Keep ValueError for date parsing errors
            return None
    
    def get_by_bleoid(self, bleoid):
        """Get message days for a specific BLEOId"""
        db = MongoDB.get_instance().get_collection('MessagesDays')
        return list(db.find({"BLEOId": bleoid}))

    def get_by_date(self, date):
        """Get message days for a specific date"""
        try:
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day)
            end_of_day = start_of_day + timedelta(days=1, microseconds=-1)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            return list(db.find({
                "date": {"$gte": start_of_day, "$lte": end_of_day}
            }))
        except ValueError:
            return None

    def get(self, request, bleoid=None, date=None):
        """Get message days by BLEOId, date, or both"""
        try:
            if bleoid and date:
                # Single message day retrieval
                message_day = self.get_by_bleoid_and_date(bleoid, date)
                if not message_day:
                    return BLEOResponse.not_found(
                        message=f"No message day found for BLEOId={bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Format the single message day
                message_day['_id'] = str(message_day['_id'])
                if isinstance(message_day['date'], datetime):
                    message_day['date'] = message_day['date'].strftime('%d-%m-%Y')
                    
                # Add quadrant info
                _add_quadrant_info(self, message_day)
                
                # Use serializer for output
                serializer = MessagesDayserializer(message_day)
                
                return BLEOResponse.success(
                    data=serializer.data,
                    message="Message day retrieved successfully"
                ).to_response()
        
            elif bleoid:
                # Get all message days for this BLEOId
                message_days = self.get_by_bleoid(bleoid)
                if not message_days:
                    return BLEOResponse.not_found(
                        message=f"No message days found for BLEOId={bleoid}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
        
            elif date:
                # Get all message days for this date
                message_days = self.get_by_date(date)
                if not message_days:
                    return BLEOResponse.not_found(
                        message=f"No message days found for date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
        
            else:
                return BLEOResponse.validation_error(
                    message="Either BLEOId or date must be provided"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Format the message days list
            for day in message_days:
                day['_id'] = str(day['_id'])
                if isinstance(day['date'], datetime):
                    day['date'] = day['date'].strftime('%d-%m-%Y')
                # Add quadrant info
                _add_quadrant_info(self, day)
            
            # Use serializer for output
            serializer = MessagesDayserializer(message_days, many=True)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Message days retrieved successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve message day(s): {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, bleoid, date):
        """Update a message day by BLEOId and date"""
        try:
            # Get existing message day
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Use serializer for input validation
            serializer = MessagesDayserializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Don't allow changing BLEOId or date
            if 'BLEOId' in validated_data:
                del validated_data['BLEOId']
            if 'date' in validated_data:
                del validated_data['date']
        
            # Update the document
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            result = db.update_one(
                {"_id": message_day['_id']},
                {"$set": validated_data}
            )
            
            if result.modified_count == 0:
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get updated document
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            # Convert ObjectId to string
            updated_message_day['_id'] = str(updated_message_day['_id'])
            
            # Format date
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
        
            # Add quadrant info
            _add_quadrant_info(self, updated_message_day)
        
            # Use serializer for response
            response_serializer = MessagesDayserializer(updated_message_day)
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day updated successfully"
            ).to_response()
        
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to update message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date):
        """Delete a message day by BLEOId and date"""
        try:
            message_day = self.get_by_bleoid_and_date(bleoid, date)
            if not message_day:
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete the document
            db = MongoDB.get_instance().get_collection('MessagesDays')
            db.delete_one({"_id": message_day['_id']})
            
            return BLEOResponse.success(
                message="Message day deleted successfully"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class MoodOptionsView(APIView):
    """API view for getting mood-related options"""
    
    def get(self, request):
        """Get energy levels, pleasantness options, and filtered moods"""
        try:
            # Get query parameters for filtering
            energy = request.query_params.get('energy')
            pleasantness = request.query_params.get('pleasantness')
            
            # Create response with all options
            response_data = {
                "energy_levels": [{"value": level.value, "label": level.value.capitalize()} 
                                 for level in EnergyLevel],
                "pleasantness_options": [{"value": option.value, "label": option.value.capitalize()} 
                                        for option in Pleasantness],
                "mood_quadrants": [{"value": quadrant.value, 
                                   "label": quadrant.value.capitalize()} 
                                   for quadrant in MoodQuadrant],
            }
            
            # Filter moods by quadrant if energy and pleasantness are provided
            if energy and pleasantness:
                try:
                    energy_enum = EnergyLevel(energy)
                    pleasantness_enum = Pleasantness(pleasantness)
                    quadrant = MoodQuadrant.from_dimensions(energy_enum, pleasantness_enum)
                    
                    # Get moods for this quadrant
                    matching_moods = [mood for mood in MoodType 
                                     if mood.quadrant == quadrant]
                    
                    response_data["filtered_moods"] = [
                        {"value": mood.value, "label": mood.value}
                        for mood in matching_moods
                    ]
                    response_data["selected_quadrant"] = quadrant.value
                except ValueError:
                    # Invalid energy or pleasantness value
                    response_data["filtered_moods"] = []
                    response_data["error"] = "Invalid energy or pleasantness value"
            else:
                # No filtering, return all moods
                response_data["all_moods"] = [
                    {"value": mood.value, "label": mood.value}
                    for mood in MoodType
                ]
            
            return BLEOResponse.success(
                data=response_data,
                message="Mood options retrieved successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve mood options: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageDayCreateView(APIView):
    """API view for creating message days with BLEOId in URL path"""
    
    def post(self, request, bleoid):
        """Create a new message day with BLEOId from URL path"""
        try:

            data = request.data.copy()

            # Add BLEOId from URL to data
            data['BLEOId'] = bleoid
            
            # Check if date is provided, if not initialize to today
            if 'date' not in data:
                now = datetime.now()
                data['date'] = now.strftime('%d-%m-%Y')

            serializer = MessagesDayserializer(data=data)
            if not serializer.is_valid():
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current date and set time to midnight
            now = datetime.now()
            message_date = datetime(now.year, now.month, now.day)
            
            # Check if entry already exists for this user and date using exact date match
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            existing_entry = db_message_days.find_one({
                "BLEOId": bleoid,
                "date": message_date
            })
            
            if existing_entry:
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Message day already exists for BLEOId {bleoid} on {message_date.strftime('%d-%m-%Y')}"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Process messages - generate IDs
            messages = data.get('messages', [])
            processed_messages = _generate_message_ids(messages)
            
            # Create MessagesDays instance with midnight date
            message_day = MessagesDays(
                BLEOId=bleoid,
                date=message_date,
                messages=processed_messages,
                mood=data.get('mood'),
                energy_level=data.get('energy_level'),
                pleasantness=data.get('pleasantness')
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
            response_serializer = MessagesDayserializer(created_message_day)
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Message day created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to create message day: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _format_message_day_for_serializer(self, message_day):
        """Format a message day document for serializer consumption"""
        if not message_day:
            return None
            
        # Convert ObjectId to string
        message_day['_id'] = str(message_day['_id'])
        
        # Format date
        if 'date' in message_day and isinstance(message_day['date'], datetime):
            message_day['date'] = message_day['date'].strftime('%d-%m-%Y')
        
        # Add quadrant info
        _add_quadrant_info(self, message_day)
        
        return message_day

    def delete(self, request, bleoid):
        """Delete all message days for a specific BLEOId"""
        try:
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"BLEOId": bleoid})
            
            if not user:
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoid} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Delete all message days for this user
            db = MongoDB.get_instance().get_collection('MessagesDays')
            result = db.delete_many({"BLEOId": bleoid})
            
            if result.deleted_count == 0:
                return BLEOResponse.not_found(
                    message=f"No message days found for BLEOId={bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            return BLEOResponse.success(
                data={"deleted_count": result.deleted_count},
                message=f"Successfully deleted {result.deleted_count} message day(s) for BLEOId={bleoid}"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete message days: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
