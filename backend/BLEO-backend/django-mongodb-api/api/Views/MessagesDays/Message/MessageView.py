from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from datetime import datetime
from models.response.BLEOResponse import BLEOResponse
from models.enums.MessageType import MessageType
from api.serializers import MessageInfosSerializer  # Import the serializer

class MessageOperationsView(APIView):
    """API view for operations on messages within a message day"""
    
    def _validate_message_type(self, msg_type):
        """Validate that the message type is part of the enum - use serializer instead"""
        return msg_type in [t.value for t in MessageType]
    
    def get_message_day(self, bleoid, date):
        """Get message day by BLEOId and date"""
        try:
            # No type conversion needed for bleoid anymore since it's a string
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            
            # Midnight timestamp
            message_date = datetime(date_obj.year, date_obj.month, date_obj.day)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            return db.find_one({
                "BLEOId": bleoid,
                "date": message_date
            })
        except ValueError:
            return None
    
    def put(self, request, bleoid, date, message_id=None):
        """Update messages with serializer validation"""
        try:
            data = request.data
            message_day = self.get_message_day(bleoid, date)
            
            if not message_day:
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            
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
                    return BLEOResponse.not_found(
                        message=f"Message with ID {message_id} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Use serializer for validation
                serializer = MessageInfosSerializer(data=data, partial=True)
                if not serializer.is_valid():
                    return BLEOResponse.validation_error(
                        message="Invalid message data",
                        errors=serializer.errors
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                # Get validated data
                validated_data = serializer.validated_data
                
                # Update the message (preserve id and any non-provided fields)
                for key, value in validated_data.items():
                    messages[message_index][key] = value
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": messages}}
                )
                
                # Prepare response
                updated_message = messages[message_index]
                response_serializer = MessageInfosSerializer(updated_message)
                
                return BLEOResponse.success(
                    data=response_serializer.data,
                    message="Message updated successfully"
                ).to_response()
            
            else:
                # Replace all messages
                if 'messages' not in data or not isinstance(data['messages'], list):
                    return BLEOResponse.validation_error(
                        message="Request must include a 'messages' array"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                # Validate each message with serializer
                new_messages = data['messages']
                processed_messages = []
                max_id = 0
                
                for i, msg in enumerate(new_messages):
                    serializer = MessageInfosSerializer(data=msg)
                    if not serializer.is_valid():
                        return BLEOResponse.validation_error(
                            message=f"Invalid message at index {i}",
                            errors=serializer.errors
                        ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                    # Get validated data
                    validated_msg = serializer.validated_data
                    
                    # Add or preserve ID
                    if 'id' in msg and isinstance(msg['id'], int):
                        msg_id = msg['id']
                    else:
                        max_id += 1
                        msg_id = max_id
                    
                    validated_msg['id'] = msg_id
                    processed_messages.append(validated_msg)
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": processed_messages}}
                )
                
                # Get updated document
                updated_message_day = db.find_one({"_id": message_day['_id']})
                
                # Format for response
                updated_message_day['_id'] = str(updated_message_day['_id'])
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
                
                # Use serializer for messages in response
                messages = updated_message_day.get('messages', [])
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                response_data = {
                    '_id': updated_message_day['_id'],
                    'BLEOId': updated_message_day['BLEOId'],
                    'date': updated_message_day['date'],
                    'messages': message_serializer.data
                }
                
                return BLEOResponse.success(
                    data=response_data,
                    message="All messages replaced successfully"
                ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to update messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date, message_id=None):
        """Delete messages"""
        try:
            message_day = self.get_message_day(bleoid, date)
            
            if not message_day:
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            
            if message_id is not None:
                # Delete specific message by ID
                message_id = int(message_id)
                messages = message_day.get('messages', [])
                updated_messages = [msg for msg in messages if msg.get('id') != message_id]
                
                if len(messages) == len(updated_messages):
                    return BLEOResponse.not_found(
                        message=f"For User with BLEOId {bleoid} and at date {date}, message with ID {message_id} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": updated_messages}}
                )
                
                # Get updated document for response
                updated_message_day = db.find_one({"_id": message_day['_id']})
                updated_message_day['_id'] = str(updated_message_day['_id'])
                
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
                
                # Serialize messages for response
                messages = updated_message_day.get('messages', [])
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                response_data = {
                    '_id': updated_message_day['_id'],
                    'BLEOId': updated_message_day['BLEOId'],
                    'date': updated_message_day['date'],
                    'messages': message_serializer.data
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
                
                # Get updated document for response
                updated_message_day = db.find_one({"_id": message_day['_id']})
                updated_message_day['_id'] = str(updated_message_day['_id'])
                
                if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                    updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
                
                response_data = {
                    '_id': updated_message_day['_id'],
                    'BLEOId': updated_message_day['BLEOId'],
                    'date': updated_message_day['date'],
                    'messages': []
                }
                
                return BLEOResponse.success(
                    data=response_data,
                    message="All messages deleted successfully"
                ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, bleoid, date):
        """Add new messages with serializer validation"""
        try:
            data = request.data
            message_day = self.get_message_day(bleoid, date)
            
            if not message_day:
                return BLEOResponse.not_found(
                    message=f"No message day found for BLEOId={bleoid} on date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            
            # Get current messages
            current_messages = message_day.get('messages', [])
            
            # Get new messages to add
            new_messages = []
            if 'messages' in data and isinstance(data['messages'], list):
                new_messages = data['messages']
            elif not isinstance(data, list):
                # Single message in request body
                new_messages = [data]
            else:
                # Array of messages directly in request body
                new_messages = data
                
            # Validate new messages with serializer
            validated_messages = []
            
            for i, msg in enumerate(new_messages):
                serializer = MessageInfosSerializer(data=msg)
                if not serializer.is_valid():
                    return BLEOResponse.validation_error(
                        message=f"Invalid message at index {i}",
                        errors=serializer.errors
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                validated_messages.append(serializer.validated_data)
            
            # Find the highest existing ID
            max_id = 0
            for msg in current_messages:
                if 'id' in msg and isinstance(msg['id'], int) and msg['id'] > max_id:
                    max_id = msg['id']
            
            # Generate IDs for new messages
            for msg in validated_messages:
                if 'id' not in msg or not isinstance(msg['id'], int):
                    max_id += 1
                    msg['id'] = max_id
                
                # Add created_at if not present
                if 'created_at' not in msg:
                    msg['created_at'] = datetime.now()
            
            # Combine existing and new messages
            updated_messages = current_messages + validated_messages
            
            # Update in database
            result = db.update_one(
                {"_id": message_day['_id']},
                {"$set": {"messages": updated_messages}}
            )
            
            # Get updated document
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            # Format for response
            updated_message_day['_id'] = str(updated_message_day['_id'])
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
            
            # Use serializer for messages in response
            messages = updated_message_day.get('messages', [])
            message_serializer = MessageInfosSerializer(messages, many=True)
            
            response_data = {
                '_id': updated_message_day['_id'],
                'BLEOId': updated_message_day['BLEOId'],
                'date': updated_message_day['date'],
                'messages': message_serializer.data
            }
            
            return BLEOResponse.success(
                data=response_data,
                message=f"{len(validated_messages)} message(s) added successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to add messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, bleoid, date=None, message_id=None):
        """Get messages with serialized output"""
        try:
            # Case 3: Specific message by ID
            if date and message_id is not None:
                message_day = self.get_message_day(bleoid, date)
                if not message_day:
                    return BLEOResponse.not_found(
                        message=f"No message day found for BLEOId={bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                message_id = int(message_id)
                for msg in message_day.get('messages', []):
                    if msg.get('id') == message_id:
                        # Use serializer for single message response
                        serializer = MessageInfosSerializer(msg)
                        return BLEOResponse.success(
                            data=serializer.data,
                            message=f"Message retrieved successfully"
                        ).to_response()
                        
                return BLEOResponse.not_found(
                    message=f"Message with ID {message_id} not found for date {date}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Case 2: All messages for a specific date
            elif date:
                message_day = self.get_message_day(bleoid, date)
                if not message_day:
                    return BLEOResponse.not_found(
                        message=f"No message day found for BLEOId={bleoid} on date {date}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                messages = message_day.get('messages', [])
                
                # Use serializer for messages array
                message_serializer = MessageInfosSerializer(messages, many=True)
                
                return BLEOResponse.success(
                    data={
                        'bleoid': bleoid,
                        'date': date,
                        'messages': message_serializer.data,
                        'count': len(messages)
                    },
                    message=f"Retrieved {len(messages)} messages for date {date}"
                ).to_response()
                
            # Case 1: All messages for this user across all dates
            else:
                db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
                
                # Find all message days for this user
                message_days = list(db.find({"BLEOId": bleoid}))
                
                if not message_days:
                    return BLEOResponse.not_found(
                        message=f"No message days found for BLEOId={bleoid}"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                # Collect all messages with their dates
                result = []
                for day in message_days:
                    date_str = day['date'].strftime('%d-%m-%Y') if isinstance(day['date'], datetime) else str(day['date'])
                    
                    for msg in day.get('messages', []):
                        # Add date info to each message
                        msg_with_date = msg.copy()
                        msg_with_date['date'] = date_str
                        result.append(msg_with_date)
                
                # Use serializer for messages array
                message_serializer = MessageInfosSerializer(result, many=True)
                
                return BLEOResponse.success(
                    data={
                        'bleoid': bleoid,
                        'messages': message_serializer.data,
                        'count': len(result),
                        'date_count': len(message_days)
                    },
                    message=f"Retrieved {len(result)} messages from {len(message_days)} dates"
                ).to_response()
                
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)