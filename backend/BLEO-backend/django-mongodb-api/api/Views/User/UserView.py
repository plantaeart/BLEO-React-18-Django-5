from rest_framework.views import APIView
from rest_framework import status
from models.User import User
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId
from models.response.BLEOResponse import BLEOResponse
from api.serializers import UserSerializer
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from utils.validation_patterns import ValidationPatterns
from rest_framework.exceptions import ValidationError
from datetime import datetime

class UserListCreateView(APIView):
    """API view for listing and creating users"""
    
    def get(self, request):
        """Get all users"""
        try:
            # Log action
            Logger.debug_system_action(
                "Getting all users",
                LogType.INFO.value,
                200
            )
            
            db = MongoDB.get_instance().get_collection('Users')
            users = list(db.find({}, {'password': 0}))  # Exclude password field
            
            # Convert ObjectId to string for JSON serialization
            for user in users:
                user['_id'] = str(user['_id'])
            
            # Serialize the users
            serializer = UserSerializer(users, many=True)
                
            # Log success
            Logger.debug_system_action(
                f"Retrieved {len(users)} users successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Users retrieved successfully"
            ).to_response(status.HTTP_200_OK)
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve users: {str(e)}",
                500, 
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve users: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new user"""
        try:
            # Log action
            Logger.debug_system_action(
                "Creating new user",
                LogType.INFO.value,
                200
            )
            
            # First check if we received any data
            if not request.data:
                Logger.debug_error(
                    "No data provided for user creation",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="No data provided. Request body is empty.",
                    errors={"request": "Empty request body"}
                ).to_response(status.HTTP_400_BAD_REQUEST)
        
            # Use the serializer for validation
            serializer = UserSerializer(data=request.data, context={'auto_generate_id': True})
            if not serializer.is_valid():
                # Enhanced error logging for BLEOID validation
                error_fields = ", ".join(serializer.errors.keys())
                
                # Check for BLEOID specific errors
                bleoid_error = None
                if 'bleoid' in serializer.errors:
                    bleoid_error = serializer.errors['bleoid']
                    Logger.debug_error(
                        f"User creation failed - BLEOID validation error: {bleoid_error}",
                        400,
                        None,
                        ErrorSourceType.SERVER.value
                    )
                else:
                    Logger.debug_error(
                        f"User creation validation failed for fields: {error_fields}",
                        400,
                        None,
                        ErrorSourceType.SERVER.value
                    )
                
                return BLEOResponse.validation_error(
                    message=f"Validation failed for fields: {error_fields}",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            # bleoid is now guaranteed to be valid format (either provided or auto-generated)
            
            # Check if email already exists
            db_users = MongoDB.get_instance().get_collection('Users')
            if db_users.find_one({"email": validated_data['email']}):
                Logger.debug_error(
                    f"User creation failed - email already exists: {validated_data['email']}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message="Email already exists"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Generate new bleoid
            while True:
                new_bleoid = User.generate_bleoid()
                # Check if ID already exists
                if not db_users.find_one({"bleoid": new_bleoid}):
                    break
        
            # Hash password
            validated_data['password'] = make_password(validated_data['password'])
        
            # Create user
            user = User(
                bleoid=new_bleoid,
                email=validated_data['email'],
                password=validated_data['password'],
                userName=validated_data.get('userName', "NewUser"),
                profilePic=validated_data.get('profilePic'),
                email_verified=validated_data.get('email_verified', False),
                bio=validated_data.get('bio'),
                preferences=validated_data.get('preferences', {})
            )
            
            # Save to MongoDB
            result = db_users.insert_one(user.to_dict())
            
            # Return created user with ID
            created_user = user.to_dict()
            del created_user['password']  # Remove password from response
            created_user['_id'] = str(result.inserted_id)
            
            # Serialize the response
            response_serializer = UserSerializer(created_user)
            
            # Log success
            Logger.debug_system_action(
                f"User created successfully: {new_bleoid}",
                LogType.SUCCESS.value,
                201
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="User created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to create user: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """API view for getting, updating and deleting a user"""
    
    def get_object(self, bleoid):
        """Get a single user by bleoid or MongoDB ObjectId"""
        db = MongoDB.get_instance().get_collection('Users')
        
        # First try bleoid (now a string)
        user = db.find_one({"bleoid": bleoid}, {'password': 0})
        
        # If not found and it's a valid ObjectId, try that
        if not user and ObjectId.is_valid(bleoid):
            user = db.find_one({"_id": ObjectId(bleoid)}, {'password': 0})
            
        return user

    def get(self, request, bleoid):
        """Get a user by BLEOID"""
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Find user
            user = self.get_object(validated_bleoid)
            
            if user is None:
                Logger.debug_error(
                    f"User with bleoid {validated_bleoid} not found",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Convert ObjectId to string
            user['_id'] = str(user['_id'])
            
            # REMOVE PASSWORD FROM RESPONSE (Security!)
            if 'password' in user:
                del user['password']
            
            # Convert datetime objects to ISO format strings
            if 'created_at' in user and hasattr(user['created_at'], 'isoformat'):
                user['created_at'] = user['created_at'].isoformat()
            if 'last_login' in user and hasattr(user['last_login'], 'isoformat'):
                user['last_login'] = user['last_login'].isoformat()
            if 'updated_at' in user and hasattr(user['updated_at'], 'isoformat'):
                user['updated_at'] = user['updated_at'].isoformat()
            
            # Serialize the user
            serializer = UserSerializer(user)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                "User retrieved successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=serializer.data,
                message="User retrieved successfully"
            ).to_response()
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message="Invalid BLEOID format in URL"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to retrieve user for bleoid={bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.server_error(
                message=f"Failed to retrieve user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, bleoid):
        """Update a user"""
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Check if user exists
            user = self.get_object(validated_bleoid)
            
            if user is None:
                Logger.debug_error(
                    f"User with bleoid {validated_bleoid} not found",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Validate update data with partial=True
            serializer = UserSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"User update validation failed: {serializer.errors}",
                    400,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Hash password if provided
            if 'password' in validated_data:
                from django.contrib.auth.hashers import make_password
                validated_data['password'] = make_password(validated_data['password'])
            
            # Add updated timestamp
            validated_data['updated_at'] = datetime.now()
            
            # Update the user in database
            db = MongoDB.get_instance().get_collection('Users')
            result = db.update_one(
                {"bleoid": validated_bleoid},
                {"$set": validated_data}
            )
            
            if result.modified_count == 0:
                Logger.debug_user_action(
                    validated_bleoid,
                    "No changes made to user",
                    LogType.INFO.value,
                    200
                )
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get updated user and return it
            updated_user = self.get_object(validated_bleoid)
            updated_user['_id'] = str(updated_user['_id'])
            
            #REMOVE PASSWORD FROM RESPONSE
            if 'password' in updated_user:
                del updated_user['password']
            
            # Convert datetime objects
            if 'created_at' in updated_user and hasattr(updated_user['created_at'], 'isoformat'):
                updated_user['created_at'] = updated_user['created_at'].isoformat()
            if 'last_login' in updated_user and hasattr(updated_user['last_login'], 'isoformat'):
                updated_user['last_login'] = updated_user['last_login'].isoformat()
            if 'updated_at' in updated_user and hasattr(updated_user['updated_at'], 'isoformat'):
                updated_user['updated_at'] = updated_user['updated_at'].isoformat()
            
            # Serialize response
            response_serializer = UserSerializer(updated_user)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                "User updated successfully",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="User updated successfully"
            ).to_response()
            
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {str(e)}",
                400,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message="Invalid BLEOID format in URL"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            Logger.debug_error(
                f"Failed to update user for bleoid={bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.server_error(
                message=f"Failed to update user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid):
        """Delete a user by bleoid with URL validation"""
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = ValidationPatterns.validate_url_bleoid(bleoid, "bleoid")
            
            # Continue with existing logic using validated_bleoid
            # Log delete action
            Logger.debug_system_action(
                f"Deleting user with bleoid: {validated_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Get database connections
            db_users = MongoDB.get_instance().get_collection('Users')
            db_links = MongoDB.get_instance().get_collection('Links')
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            
            # First check if user exists
            user = db_users.find_one({"bleoid": validated_bleoid})
            if not user:
                # Log user not found
                Logger.debug_error(
                    f"User not found with bleoid: {validated_bleoid} during deletion",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Log the start of cascade deletion
            Logger.debug_system_action(
                f"Starting cascade deletion for user with bleoid: {validated_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # STEP 1: Find any links where this user is bleoidPartner2
            related_links = list(db_links.find({"bleoidPartner2": validated_bleoid}))
            
            # STEP 2: Update those links to set bleoidPartner2 to null
            if related_links:
                result = db_links.update_many(
                    {"bleoidPartner2": validated_bleoid},
                    {"$set": {"bleoidPartner2": None}}
                )
                # Log link updates
                Logger.debug_system_action(
                    f"Updated {result.modified_count} links that referenced the deleted user {validated_bleoid}",
                    LogType.INFO.value,
                    200
                )
            
            # STEP 3: Delete the user's own link where they are bleoidPartner1
            link_delete_result = db_links.delete_one({"bleoidPartner1": validated_bleoid})
            link_deleted = link_delete_result.deleted_count
            
            # Log link deletion
            Logger.debug_system_action(
                f"Deleted {link_deleted} primary links for user {validated_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # STEP 4: Delete all MessagesDays associated with this user
            message_days_result = db_message_days.delete_many({"from_bleoid": validated_bleoid})
            message_days_count = message_days_result.deleted_count
            
            # Log message days deletion
            Logger.debug_system_action(
                f"Deleted {message_days_count} message days for user {validated_bleoid}",
                LogType.INFO.value,
                200
            )
            
            # STEP 5: Finally delete the user
            result = db_users.delete_one({"bleoid": validated_bleoid})
            
            # Log final user deletion
            if result.deleted_count > 0:
                Logger.debug_system_action(
                    f"User with bleoid: {validated_bleoid} deleted successfully",
                    LogType.SUCCESS.value,
                    200
                )
            else:
                # This should not happen as we checked for user existence above
                Logger.debug_error(
                    f"Failed to delete user with bleoid: {validated_bleoid}. User record not found during final deletion.",
                    500,
                    None,
                    ErrorSourceType.SERVER.value
                )
            
            return BLEOResponse.success(
                message=f"User deleted successfully. Also removed {message_days_count} message day records."
            ).to_response(status.HTTP_200_OK)
            
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
            # Log error
            Logger.debug_error(
                f"Failed to delete user with bleoid {bleoid}: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)