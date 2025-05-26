from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from datetime import datetime
from models.response.BLEOResponse import BLEOResponse
from models.enums.MessageType import MessageType

class MessageOperationsView(APIView):
    """API view for operations on messages within a message day"""
    
    def _validate_message_type(self, msg_type):
        """Validate that the message type is part of the enum"""
        valid_types = [item.value for item in MessageType]
        return msg_type in valid_types
    
    def get_message_day(self, bleoid, date):
        """Get message day by BLEOId and date"""
        try:
            bleoid_int = bleoid
            date_obj = datetime.strptime(date, '%d-%m-%Y')
            
            # Midnight timestamp
            message_date = datetime(date_obj.year, date_obj.month, date_obj.day)
            
            db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
            return db.find_one({
                "BLEOId": bleoid_int,
                "date": message_date
            })
        except (ValueError, TypeError):
            return None
    
    def put(self, request, bleoid, date, message_id=None):
        """
        Update messages:
        - If message_id is provided: Update specific message
        - Otherwise: Replace all messages
        """
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
                
                # Validate message type if present
                if 'type' in data and not self._validate_message_type(data['type']):
                    return BLEOResponse.validation_error(
                        message=f"Invalid message type: '{data['type']}'. Valid types are: {', '.join([item.value for item in MessageType])}"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                # Update the message
                data['id'] = message_id  # Ensure ID remains the same
                messages[message_index] = data
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": messages}}
                )
                
                response_message = "Message updated successfully"
            else:
                # Replace all messages - generate IDs for new messages
                new_messages = data.get('messages', [])
                
                # Validate message types
                for i, msg in enumerate(new_messages):
                    if 'type' in msg and not self._validate_message_type(msg['type']):
                        return BLEOResponse.validation_error(
                            message=f"Message at index {i} has invalid type: '{msg['type']}'. Valid types are: {', '.join([item.value for item in MessageType])}"
                        ).to_response(status.HTTP_400_BAD_REQUEST)
                
                # Generate IDs for any messages that don't have them
                processed_messages = []
                max_id = 0
                
                for msg in new_messages:
                    if 'id' in msg and isinstance(msg['id'], int):
                        msg_id = msg['id']
                    else:
                        max_id += 1
                        msg_id = max_id
                        msg['id'] = msg_id
                    
                    processed_messages.append(msg)
                
                # Update in database
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": processed_messages}}
                )
                
                response_message = "All messages replaced successfully"
            
            # Get updated document
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            # Convert ObjectId to string
            updated_message_day['_id'] = str(updated_message_day['_id'])
            
            # Format date as ISO
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
            
            return BLEOResponse.success(
                data=updated_message_day,
                message=response_message
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to update messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid, date, message_id=None):
        """
        Delete messages:
        - If message_id is provided: Delete specific message
        - Otherwise: Delete all messages
        """
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
                
                response_message = f"Message with ID {message_id} deleted successfully"
            else:
                # Delete all messages
                result = db.update_one(
                    {"_id": message_day['_id']},
                    {"$set": {"messages": []}}
                )
                
                response_message = "All messages deleted successfully"
            
            # Get updated document
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            # Convert ObjectId to string
            updated_message_day['_id'] = str(updated_message_day['_id'])
            
            # Format date as ISO
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
            
            return BLEOResponse.success(
                data=updated_message_day,
                message=response_message
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, bleoid, date):
        """Add new messages to the existing ones"""
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
                
            # Validate required fields for each message
            for i, msg in enumerate(new_messages):
                missing_fields = []
                
                if 'title' not in msg or not msg['title']:
                    missing_fields.append('title')
                    
                if 'text' not in msg or not msg['text']:
                    missing_fields.append('text')
                    
                if 'type' not in msg or not msg['type']:
                    missing_fields.append('type')
                elif not self._validate_message_type(msg['type']):
                    return BLEOResponse.validation_error(
                        message=f"Invalid message type: '{msg['type']}'. Valid types are: {', '.join([item.value for item in MessageType])}"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                if missing_fields:
                    index_info = f"at index {i}" if len(new_messages) > 1 else ""
                    return BLEOResponse.validation_error(
                        message=f"Message {index_info} is missing required fields: {', '.join(missing_fields)}"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Find the highest existing ID
            max_id = 0
            for msg in current_messages:
                if 'id' in msg and isinstance(msg['id'], int) and msg['id'] > max_id:
                    max_id = msg['id']
            
            # Generate IDs for new messages
            for msg in new_messages:
                if 'id' not in msg or not isinstance(msg['id'], int):
                    max_id += 1
                    msg['id'] = max_id
            
            # Combine existing and new messages
            updated_messages = current_messages + new_messages
            
            # Update in database
            result = db.update_one(
                {"_id": message_day['_id']},
                {"$set": {"messages": updated_messages}}
            )
            
            # Get updated document
            updated_message_day = db.find_one({"_id": message_day['_id']})
            
            # Convert ObjectId to string
            updated_message_day['_id'] = str(updated_message_day['_id'])
            
            # Format date as ISO
            if 'date' in updated_message_day and isinstance(updated_message_day['date'], datetime):
                updated_message_day['date'] = updated_message_day['date'].strftime('%d-%m-%Y')
            
            return BLEOResponse.success(
                data=updated_message_day,
                message=f"{len(new_messages)} message(s) added successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to add messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, bleoid, date=None, message_id=None):
        """
        Get messages with different filtering options:
        1. If only bleoid: Get all messages for this user across all dates
        2. If bleoid and date: Get all messages for this date
        3. If bleoid, date and message_id: Get specific message
        """
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
                        return BLEOResponse.success(
                            data=msg,
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
                return BLEOResponse.success(
                    data={
                        'bleoid': bleoid,
                        'date': date,
                        'messages': messages,
                        'count': len(messages)
                    },
                    message=f"Retrieved {len(messages)} messages for date {date}"
                ).to_response()
                
            # Case 1: All messages for this user across all dates
            else:
                bleoid_int = bleoid
                db = MongoDB.get_instance().get_collection('MessagesDays')  # Fixed collection name
                
                # Find all message days for this user
                message_days = list(db.find({"BLEOId": bleoid_int}))
                
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
                
                return BLEOResponse.success(
                    data={
                        'bleoid': bleoid,
                        'messages': result,
                        'count': len(result),
                        'date_count': len(message_days)
                    },
                    message=f"Retrieved {len(result)} messages from {len(message_days)} dates"
                ).to_response()
                
        except ValueError:
            return BLEOResponse.validation_error(
                message="Invalid parameters: BLEOId must be a number, message_id must be a number"
            ).to_response(status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve messages: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)