from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from datetime import datetime
from models.response.BLEOResponse import BLEOResponse
from models.enums.MessageType import MessageType
from api.serializers import MessageInfosSerializer
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
from models.enums.MoodQuadrantType import MoodQuadrantType
from utils.validation_patterns import ValidationPatterns, ValidationRules
from rest_framework.exceptions import ValidationError
from utils.validation_patterns import ValidationPatterns

class MessageOperationsView(APIView):
    """API view for operations on messages within a message day"""
    
    def get_message_day(self, bleoid, date):
        """Get message day by bleoid and date with validation"""
        try:
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            date_obj = datetime.strptime(date, ValidationRules.STANDARD_DATE_FORMAT)
            message_date = datetime(date_obj.year, date_obj.month, date_obj.day)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            return db.find_one({
                "from_bleoid": validated_bleoid,
                "date": message_date
            })
        except Exception:
            return None
    
    def put(self, request, bleoid, date, message_id=None):
        """Update messages with URL BLEOID validation"""
        validated_bleoid = bleoid  # Fallback value
        
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Log request
            if message_id is not None:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Updating message with ID={message_id} for date {date}",
                    LogType.INFO.value,
                    200
                )
            else:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Replacing all messages for date {date}",
                    LogType.INFO.value,
                    200
                )
            
            data = request.data
            message_day = self.get_message_day(validated_bleoid, date)
            
            if not message_day:
                Logger.debug_error(
                    f"No message day found for bleoid={validated_bleoid} on date {date} during message update",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No message day found for bleoid={validated_bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            
            if message_id is not None:
                # Update specific message by ID
                message_id = int(message_id)
                messages = message_day.get('messages', [])
                message_index = None
                
                for i, msg in enumerate(messages):
                    if msg.get('id') == message_id:
                        message_index = i
                        break
                
                if message_index is None:
                    Logger.debug_error(
                        f"Message with ID={message_id} not found for bleoid={validated_bleoid} on date {date}",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"Message with ID {message_id} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Use serializer for validation
                serializer = MessageInfosSerializer(data=data, partial=True)
                if not serializer.is_valid():
                    error_details = []
                    if 'type' in serializer.errors:
                        error_details.append(f"Message type: {serializer.errors['type']}")
                    
                    Logger.debug_error(
                        f"Invalid data when updating message ID={message_id}: {', '.join(error_details)}",
                        400,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.validation_error(
                        message="Invalid message data",
                        errors=serializer.errors
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                validated_data = serializer.validated_data
                
                # Update the message (preserve id and any non-provided fields)
                for key, value in validated_data.items():
                    messages[message_index][key] = value
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": messages}}
                )
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Message ID={message_id} updated successfully for date {date}",
                    LogType.SUCCESS.value,
                    200
                )
                
                updated_message = messages[message_index]
                response_serializer = MessageInfosSerializer(updated_message)
                
                return BLEOResponse.success(
                    data=response_serializer.data,
                    message="Message updated successfully"
                ).to_response()
            
            else:
                # Replace all messages
                if 'messages' not in data or not isinstance(data['messages'], list):
                    Logger.debug_error(
                        f"Missing 'messages' array when replacing messages for bleoid={validated_bleoid} on date {date}",
                        400,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.validation_error(
                        message="Request must include a 'messages' array"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                new_messages = data['messages']
                processed_messages = []
                max_id = 0
                
                for i, msg in enumerate(new_messages):
                    serializer = MessageInfosSerializer(data=msg)
                    if not serializer.is_valid():
                        Logger.debug_error(
                            f"Invalid message at index {i} when replacing messages: {serializer.errors}",
                            400,
                            validated_bleoid,
                            ErrorSourceType.SERVER.value
                        )
                        
                        return BLEOResponse.validation_error(
                            message=f"Invalid message at index {i}",
                            errors=serializer.errors
                        ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                    validated_msg = serializer.validated_data
                    
                    if 'id' in msg and isinstance(msg['id'], int):
                        msg_id = msg['id']
                    else:
                        max_id += 1
                        msg_id = max_id
                    
                    validated_msg['id'] = msg_id
                    processed_messages.append(validated_msg)
                
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": processed_messages}}
                )
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Replaced all messages for date {date} - now {len(processed_messages)} messages",
                    LogType.SUCCESS.value,
                    200
                )
                
                updated_message_day = db.find_one({"_id": message_day['_id']})
                
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
                messages = updated_message_day.get('messages', [])
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                response_data = {
                    'from_bleoid': updated_message_day['from_bleoid'],
                    'to_bleoid': updated_message_day.get('to_bleoid'),
                    'date': updated_message_day['date'],
                    'messages': message_serializer.data,
                    'mood': updated_message_day.get('mood'),
                    'energy_level': updated_message_day.get('energy_level'),
                    'pleasantness': updated_message_day.get('pleasantness')
                }
                
                return BLEOResponse.success(
                    data=response_data,
                    message="All messages replaced successfully"
                ).to_response()
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {bleoid} - {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format: {bleoid}"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to update message(s) for bleoid={validated_bleoid} on date {date}: {str(e)}",
                500,
                validated_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to update messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date, message_id=None):
        """Delete messages with URL BLEOID validation"""
        validated_bleoid = bleoid  # Fallback value
        
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Log request
            if message_id is not None:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Deleting message with ID={message_id} for date {date}",
                    LogType.INFO.value,
                    200
                )
            else:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Deleting all messages for date {date}",
                    LogType.INFO.value,
                    200
                )
            
            message_day = self.get_message_day(validated_bleoid, date)
            
            if not message_day:
                Logger.debug_error(
                    f"No message day found for bleoid={validated_bleoid} on date {date} during message deletion",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No message day found for bleoid={validated_bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            
            if message_id is not None:
                # Delete specific message by ID
                message_id = int(message_id)
                messages = message_day.get('messages', [])
                updated_messages = [msg for msg in messages if msg.get('id') != message_id]
                
                if len(messages) == len(updated_messages):
                    Logger.debug_error(
                        f"Message with ID={message_id} not found for bleoid={validated_bleoid} on date {date} during deletion",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"For User with bleoid {validated_bleoid} and at date {date}, message with ID {message_id} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": updated_messages}}
                )
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Message with ID={message_id} deleted successfully from date {date}",
                    LogType.SUCCESS.value,
                    200
                )
                
                updated_message_day = db.find_one({"_id": message_day['_id']})
                
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
                messages = updated_message_day.get('messages', [])
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                response_data = {
                    'from_bleoid': updated_message_day['from_bleoid'],
                    'to_bleoid': updated_message_day.get('to_bleoid'),
                    'date': updated_message_day['date'],
                    'messages': message_serializer.data,
                    'mood': updated_message_day.get('mood'),
                    'energy_level': updated_message_day.get('energy_level'),
                    'pleasantness': updated_message_day.get('pleasantness')
                }
                
                return BLEOResponse.success(
                    data=response_data,
                    message=f"Message with ID {message_id} deleted successfully"
                ).to_response()
            else:
                # Delete all messages
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": []}}
                )
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"All messages deleted successfully for date {date}",
                    LogType.SUCCESS.value,
                    200
                )
                
                updated_message_day = db.find_one({"_id": message_day['_id']})
                
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
                
                response_data = {
                    'from_bleoid': updated_message_day['from_bleoid'],
                    'to_bleoid': updated_message_day.get('to_bleoid'),
                    'date': updated_message_day['date'],
                    'messages': [],
                    'mood': updated_message_day.get('mood'),
                    'energy_level': updated_message_day.get('energy_level'),
                    'pleasantness': updated_message_day.get('pleasantness')
                }
                
                return BLEOResponse.success(
                    data=response_data,
                    message="All messages deleted successfully"
                ).to_response()
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {bleoid} - {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format: {bleoid}"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to delete message(s) for bleoid={validated_bleoid} on date {date}: {str(e)}",
                500,
                validated_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, bleoid, date):
        """Add new messages with URL BLEOID validation"""
        validated_bleoid = bleoid  # Fallback value
        
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            Logger.debug_user_action(
                validated_bleoid,
                f"Adding new message(s) for date {date}",
                LogType.INFO.value,
                200
            )
            
            data = request.data
            message_day = self.get_message_day(validated_bleoid, date)
            
            if not message_day:
                Logger.debug_error(
                    f"No message day found for bleoid={validated_bleoid} on date {date} when adding messages",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No message day found for bleoid={validated_bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')
            
            current_messages = message_day.get('messages', [])
            
            new_messages = []
            if 'messages' in data and isinstance(data['messages'], list):
                new_messages = data['messages']
            elif not isinstance(data, list):
                new_messages = [data]
            else:
                new_messages = data
                
            validated_messages = []
            
            for i, msg in enumerate(new_messages):
                serializer = MessageInfosSerializer(data=msg)
                if not serializer.is_valid():
                    Logger.debug_error(
                        f"Invalid message at index {i} when adding messages: {serializer.errors}",
                        400,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.validation_error(
                        message=f"Invalid message at index {i}",
                        errors=serializer.errors
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                validated_messages.append(serializer.validated_data)
            
            max_id = 0
            for msg in current_messages:
                if 'id' in msg and isinstance(msg['id'], int) and msg['id'] > max_id:
                    max_id = msg['id']
            
            for msg in validated_messages:
                if 'id' not in msg or not isinstance(msg['id'], int):
                    max_id += 1
                    msg['id'] = max_id
                
                if 'created_at' not in msg:
                    msg['created_at'] = datetime.now()
            
            updated_messages = current_messages + validated_messages
            
            db.update_one(
                {"_id": message_day['_id']},
                {"$set": {"messages": updated_messages}}
            )
            
            Logger.debug_user_action(
                validated_bleoid,
                f"Added {len(validated_messages)} new message(s) for date {date}",
                LogType.SUCCESS.value,
                201
            )
            
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT)
            
            messages = updated_message_day.get('messages', [])

            for msg in messages:
                if 'created_at' in msg and isinstance(msg['created_at'], datetime):
                    msg['created_at'] = msg['created_at'].strftime('%Y-%m-%dT%H:%M:%S')

            message_serializer = MessageInfosSerializer(messages, many=True)
            
            response_data = {
                'from_bleoid': updated_message_day['from_bleoid'],
                'to_bleoid': updated_message_day.get('to_bleoid'),
                'date': updated_message_day['date'],
                'messages': message_serializer.data,
                'mood': updated_message_day.get('mood'),
                'energy_level': updated_message_day.get('energy_level'),
                'pleasantness': updated_message_day.get('pleasantness')
            }
            
            return BLEOResponse.success(
                data=response_data,
                message=f"{len(validated_messages)} message(s) added successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {bleoid} - {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format: {bleoid}"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to add message(s) for bleoid={validated_bleoid} on date {date}: {str(e)}",
                500,
                validated_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to add messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, bleoid, date=None, message_id=None):
        """Get messages with URL BLEOID validation"""
        validated_bleoid = bleoid  # Fallback value
        
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Log request based on which case we're handling
            if date and message_id is not None:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Getting message with ID={message_id} for date {date}",
                    LogType.INFO.value,
                    200
                )
            elif date:
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Getting all messages for date {date}",
                    LogType.INFO.value,
                    200
                )
            else:
                Logger.debug_user_action(
                    validated_bleoid,
                    "Getting all messages across all dates",
                    LogType.INFO.value,
                    200
                )
            
            # Case 3: Specific message by ID
            if date and message_id is not None:
                message_day = self.get_message_day(validated_bleoid, date)
                if not message_day:
                    Logger.debug_error(
                        f"No message day found for bleoid={validated_bleoid} on date {date} when getting message {message_id}",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"No message day found for bleoid={validated_bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                message_id = int(message_id)
                for msg in message_day.get('messages', []):
                    if msg.get('id') == message_id:
                        Logger.debug_user_action(
                            validated_bleoid,
                            f"Message with ID={message_id} retrieved successfully for date {date}",
                            LogType.SUCCESS.value,
                            200
                        )
                        
                        serializer = MessageInfosSerializer(msg)
                        return BLEOResponse.success(
                            data=serializer.data,
                            message=f"Message retrieved successfully"
                        ).to_response()
                
                Logger.debug_error(
                    f"Message with ID={message_id} not found for bleoid={validated_bleoid} on date {date}",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"Message with ID {message_id} not found for date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Case 2: All messages for a specific date
            elif date:
                message_day = self.get_message_day(validated_bleoid, date)
                if not message_day:
                    Logger.debug_error(
                        f"No message day found for bleoid={validated_bleoid} on date {date} when listing messages",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"No message day found for bleoid={validated_bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                messages = message_day.get('messages', [])
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Retrieved {len(messages)} messages for date {date}",
                    LogType.SUCCESS.value,
                    200
                )
                
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                quadrant = None
                if 'energy_level' in message_day and message_day['energy_level'] and 'pleasantness' in message_day and message_day['pleasantness']:
                    try:
                        energy = EnergyLevelType(message_day['energy_level'])
                        pleasant = PleasantnessType(message_day['pleasantness'])
                        quadrant = MoodQuadrantType.from_dimensions(energy, pleasant).value
                    except (ValueError, KeyError):
                        pass
                
                return BLEOResponse.success(
                    data={
                        'from_bleoid': validated_bleoid,
                        'to_bleoid': message_day.get('to_bleoid'),
                        'date': date,
                        'messages': message_serializer.data,
                        'count': len(messages),
                        'mood': message_day.get('mood'),
                        'energy_level': message_day.get('energy_level'),
                        'pleasantness': message_day.get('pleasantness'),
                        'quadrant': quadrant
                    },
                    message=f"Retrieved {len(messages)} messages for date {date}"
                ).to_response()
                
            # Case 1: All messages for this user across all dates
            else:
                db = MongoDB.get_instance().get_collection('MessagesDays')
                
                message_days = list(db.find({"from_bleoid": validated_bleoid}))
                
                if not message_days:
                    Logger.debug_error(
                        f"No message days found for bleoid={validated_bleoid}",
                        404,
                        validated_bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"No message days found for bleoid={validated_bleoid}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                result = []
                for day in message_days:
                    date_str = day['date'].strftime(ValidationRules.STANDARD_DATE_FORMAT) if isinstance(day['date'], datetime) else str(day['date'])
                    
                    quadrant = None
                    if 'energy_level' in day and day['energy_level'] and 'pleasantness' in day and day['pleasantness']:
                        try:
                            energy = EnergyLevelType(day['energy_level'])
                            pleasant = PleasantnessType(day['pleasantness'])
                            quadrant = MoodQuadrantType.from_dimensions(energy, pleasant).value
                        except (ValueError, KeyError):
                            pass
                    
                    for msg in day.get('messages', []):
                        msg_with_date = msg.copy()
                        msg_with_date['date'] = date_str
                        msg_with_date['from_bleoid'] = day.get('from_bleoid')
                        msg_with_date['to_bleoid'] = day.get('to_bleoid')
                        msg_with_date['mood'] = day.get('mood')
                        msg_with_date['energy_level'] = day.get('energy_level')
                        msg_with_date['pleasantness'] = day.get('pleasantness')
                        msg_with_date['quadrant'] = quadrant
                        result.append(msg_with_date)
                
                Logger.debug_user_action(
                    validated_bleoid,
                    f"Retrieved {len(result)} messages from {len(message_days)} dates",
                    LogType.SUCCESS.value,
                    200
                )
                
                message_serializer = MessageInfosSerializer(result, many=True)
                
                return BLEOResponse.success(
                    data={
                        'from_bleoid': validated_bleoid,
                        'messages': message_serializer.data,
                        'count': len(result),
                        'date_count': len(message_days)
                    },
                    message=f"Retrieved {len(result)} messages from {len(message_days)} dates"
                ).to_response()
        
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {bleoid} - {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format: {bleoid}"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to retrieve message(s) for bleoid={validated_bleoid}" + 
                (f" on date {date}" if date else "") +
                (f" with ID={message_id}" if message_id is not None else "") +
                f": {str(e)}",
                500,
                validated_bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)