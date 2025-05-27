from rest_framework.views import APIView
from rest_framework import status
from models.User import User
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password, check_password
from bson import ObjectId
from models.response.BLEOResponse import BLEOResponse
from api.serializers import UserSerializer  # Import the serializer

class UserListCreateView(APIView):
    """API view for listing and creating users"""
    
    def get(self, request):
        """Get all users"""
        try:
            db = MongoDB.get_instance().get_collection('Users')
            users = list(db.find({}, {'password': 0}))  # Exclude password field
            
            # Convert ObjectId to string for JSON serialization
            for user in users:
                user['_id'] = str(user['_id'])
            
            # Serialize the users
            serializer = UserSerializer(users, many=True)
                
            return BLEOResponse.success(
                data=serializer.data,
                message="Users retrieved successfully"
            ).to_response()
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve users: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new user"""
        try:
            # First check if we received any data
            if not request.data:
                return BLEOResponse.validation_error(
                    message="No data provided. Request body is empty.",
                    errors={"request": "Empty request body"}
                ).to_response(status.HTTP_400_BAD_REQUEST)
        
            # Use the serializer for validation
            serializer = UserSerializer(data=request.data)
            if not serializer.is_valid():
                # Get field names with errors
                error_fields = ", ".join(serializer.errors.keys())
                
                # More descriptive error message
                return BLEOResponse.validation_error(
                    message=f"Validation failed for fields: {error_fields}",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get validated data
            validated_data = serializer.validated_data
            
            # Check if email already exists
            db_users = MongoDB.get_instance().get_collection('Users')
            if db_users.find_one({"email": validated_data['email']}):
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message="Email already exists"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Generate new BLEOId
            while True:
                new_bleoid = User.generate_bleoid()
                # Check if ID already exists
                if not db_users.find_one({"BLEOId": new_bleoid}):
                    break
        
            # Hash password
            validated_data['password'] = make_password(validated_data['password'])
        
            # Create user
            user = User(
                BLEOId=new_bleoid,
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
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="User created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to create user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """API view for getting, updating and deleting a user"""
    
    def get_object(self, bleoid):
        """Get a single user by BLEOId or MongoDB ObjectId"""
        db = MongoDB.get_instance().get_collection('Users')
        
        # First try BLEOId (now a string)
        user = db.find_one({"BLEOId": bleoid}, {'password': 0})
        
        # If not found and it's a valid ObjectId, try that
        if not user and ObjectId.is_valid(bleoid):
            user = db.find_one({"_id": ObjectId(bleoid)}, {'password': 0})
            
        return user

    def get(self, request, bleoid):
        """Get a single user by BLEOId"""
        try:
            user = self.get_object(bleoid)
            
            if user is None:
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Convert ObjectId to string
            user['_id'] = str(user['_id'])
            
            # Serialize the user
            serializer = UserSerializer(user)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="User retrieved successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, bleoid):
        """Update a user by BLEOId"""
        try:
            # Check if user exists
            user = self.get_object(bleoid)
            if user is None:
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Use serializer for validation
            serializer = UserSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Hash password if it was provided
            if 'password' in validated_data:
                validated_data['password'] = make_password(validated_data['password'])
        
            # Don't allow changing BLEOId
            if 'BLEOId' in validated_data:
                del validated_data['BLEOId']
        
            # Update user
            db = MongoDB.get_instance().get_collection('Users')
            result = db.update_one(
                {"BLEOId": bleoid}, 
                {'$set': validated_data}
            )
            
            if result.modified_count == 0:
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
                
            # Get and return updated user
            updated_user = self.get_object(bleoid)
            updated_user['_id'] = str(updated_user['_id'])
        
            # Serialize the response
            response_serializer = UserSerializer(updated_user)
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="User updated successfully"
            ).to_response()
        
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to update user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid):
        """Delete a user by BLEOId and clean up related data"""
        try:         
            # Get database connections
            db_users = MongoDB.get_instance().get_collection('Users')
            db_links = MongoDB.get_instance().get_collection('Links')
            db_message_days = MongoDB.get_instance().get_collection('MessagesDays')
            
            # First check if user exists
            user = db_users.find_one({"BLEOId": bleoid})
            if not user:
                return BLEOResponse.not_found(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # STEP 1: Find any links where this user is BLEOIdPartner2
            related_links = list(db_links.find({"BLEOIdPartner2": bleoid}))
            
            # STEP 2: Update those links to set BLEOIdPartner2 to null
            if related_links:
                result = db_links.update_many(
                    {"BLEOIdPartner2": bleoid},
                    {"$set": {"BLEOIdPartner2": None}}
                )
                print(f"Updated {result.modified_count} links that referenced the deleted user")
            
            # STEP 3: Delete the user's own link where they are BLEOIdPartner1
            db_links.delete_one({"BLEOIdPartner1": bleoid})
            
            # STEP 4: Delete all MessagesDays associated with this user
            message_days_result = db_message_days.delete_many({"BLEOId": bleoid})
            message_days_count = message_days_result.deleted_count
            
            # STEP 5: Finally delete the user
            result = db_users.delete_one({"BLEOId": bleoid})
            
            return BLEOResponse.success(
                message=f"User deleted successfully. Also removed {message_days_count} message day records."
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete user: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)