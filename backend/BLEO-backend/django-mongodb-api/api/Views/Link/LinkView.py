from rest_framework.views import APIView
from rest_framework import status
from models.Link import Link
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime
from models.response.BLEOResponse import BLEOResponse
from api.serializers import LinkSerializer
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class LinkListCreateView(APIView):
    """API view for listing and creating links"""
    
    def get(self, request):
        """Get all links"""
        try:
            # Log request
            Logger.debug_system_action(
                "Getting all links",
                LogType.INFO.value,
                200
            )
            
            db = MongoDB.get_instance().get_collection('Links')
            links = list(db.find({}))
            
            # Convert ObjectId to string for JSON serialization
            for link in links:
                link['_id'] = str(link['_id'])
            
            # Serialize the links
            serializer = LinkSerializer(links, many=True)
            
            # Log success
            Logger.debug_system_action(
                f"Retrieved {len(links)} links successfully",
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                data=serializer.data,
                message="Links retrieved successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve links: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve links: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new link with BLEOIdPartner1 required, BLEOIdPartner2 optional"""
        try:
            # Get BLEOIdPartner1 from request data
            bleoidPartner1 = request.data.get('BLEOIdPartner1')
            
            # Log request
            Logger.debug_system_action(
                f"Creating new link for BLEOIdPartner1={bleoidPartner1}",
                LogType.INFO.value,
                200
            )
            
            # Use serializer for validation
            serializer = LinkSerializer(data=request.data)
            if not serializer.is_valid():
                # Log validation errors
                Logger.debug_error(
                    f"Link creation validation failed: {serializer.errors}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            validated_data = serializer.validated_data
            bleoidPartner1 = validated_data['BLEOIdPartner1']
            bleoidPartner2 = validated_data.get('BLEOIdPartner2')
            
            # Check if users exist
            db_users = MongoDB.get_instance().get_collection('Users')
            user1 = db_users.find_one({"BLEOId": bleoidPartner1})
            
            if not user1:
                # Log user not found error
                Logger.debug_error(
                    f"User with BLEOId {bleoidPartner1} not found when creating link",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoidPartner1} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            if bleoidPartner2:
                user2 = db_users.find_one({"BLEOId": bleoidPartner2})
                if not user2:
                    # Log second user not found error
                    Logger.debug_error(
                        f"User with BLEOId {bleoidPartner2} not found when creating link",
                        404,
                        bleoidPartner1,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"User with BLEOId {bleoidPartner2} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Check if link already exists with this BLEOIdPartner1
            db_links = MongoDB.get_instance().get_collection('Links')
            existing_link = db_links.find_one({"BLEOIdPartner1": bleoidPartner1})
            
            if existing_link:
                # Log duplicate link error
                Logger.debug_error(
                    f"Link with BLEOIdPartner1={bleoidPartner1} already exists",
                    409,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Link with BLEOIdPartner1={bleoidPartner1} already exists"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Create link
            link = Link(
                BLEOIdPartner1=bleoidPartner1,
                BLEOIdPartner2=bleoidPartner2,
                status=validated_data.get('status', "pending"),
                created_at=validated_data.get('created_at'),
                updated_at=validated_data.get('updated_at')
            )
            
            # Save to MongoDB
            result = db_links.insert_one(link.to_dict())
            
            # Return created link with ID
            created_link = link.to_dict()
            created_link['_id'] = str(result.inserted_id)
            
            # Serialize response
            response_serializer = LinkSerializer(created_link)
            
            # Log success
            Logger.debug_user_action(
                bleoidPartner1,
                f"Link created successfully" + (f" with partner {bleoidPartner2}" if bleoidPartner2 else ""),
                LogType.SUCCESS.value,
                201
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Link created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            # Get BLEOIdPartner1 if available
            bleoidPartner1 = None
            try:
                bleoidPartner1 = request.data.get('BLEOIdPartner1')
            except:
                pass
                
            # Log error
            Logger.debug_error(
                f"Failed to create link: {str(e)}",
                500,
                bleoidPartner1,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to create link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class LinkDetailView(APIView):
    """API view for getting, updating and deleting a link"""
    
    def get_object(self, bleoidPartner1):
        """Get a single link by BLEOIdPartner1"""
        db = MongoDB.get_instance().get_collection('Links')
        return db.find_one({"BLEOIdPartner1": bleoidPartner1})
    
    def get(self, request, bleoidPartner1):
        """Get a link by BLEOIdPartner1"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Getting link for BLEOIdPartner1={bleoidPartner1}",
                LogType.INFO.value,
                200
            )
            
            # Get link by BLEOIdPartner1 (now a string)
            link = self.get_object(bleoidPartner1)
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOIdPartner1={bleoidPartner1}",
                    404,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Convert ObjectId to string for JSON serialization
            link['_id'] = str(link['_id'])
            
            # Serialize the link
            serializer = LinkSerializer(link)
            
            # Log success
            Logger.debug_user_action(
                bleoidPartner1,
                "Link retrieved successfully",
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                data=serializer.data,
                message="Link retrieved successfully"
            ).to_response()
                
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve link for BLEOIdPartner1={bleoidPartner1}: {str(e)}",
                500,
                bleoidPartner1,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)           
    
    def put(self, request, bleoidPartner1):
        """Update a link"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Updating link for BLEOIdPartner1={bleoidPartner1}",
                LogType.INFO.value,
                200
            )
            
            # Get the link
            link = self.get_object(bleoidPartner1)
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOIdPartner1={bleoidPartner1} during update",
                    404,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current BLEOIdPartner2 value
            current_bleoidPartner2 = link.get('BLEOIdPartner2')
            
            # Validate with serializer
            serializer = LinkSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                # Log validation error
                Logger.debug_error(
                    f"Link update validation failed: {serializer.errors}",
                    400,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            validated_data = serializer.validated_data
            
            # Don't allow changing BLEOIdPartner1
            if 'BLEOIdPartner1' in validated_data:
                del validated_data['BLEOIdPartner1']
                
            # Handle new BLEOIdPartner2
            new_bleoidPartner2 = validated_data.get('BLEOIdPartner2')
            
            if new_bleoidPartner2:
                # Check if user exists
                db_users = MongoDB.get_instance().get_collection('Users')
                user2 = db_users.find_one({"BLEOId": new_bleoidPartner2})
                if not user2:
                    # Log user not found error
                    Logger.debug_error(
                        f"User with BLEOId {new_bleoidPartner2} not found during link update",
                        404,
                        bleoidPartner1,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"User with BLEOId {new_bleoidPartner2} not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                    
                # Check if the target user has a link
                db = MongoDB.get_instance().get_collection('Links')
                partner2_link = db.find_one({"BLEOIdPartner1": new_bleoidPartner2})
                if not partner2_link:
                    # Log partner link not found error
                    Logger.debug_error(
                        f"User with BLEOId {new_bleoidPartner2} does not have a link",
                        404,
                        bleoidPartner1,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.not_found(
                        message=f"User with BLEOId {new_bleoidPartner2} does not have a link"
                    ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Update the link
            db = MongoDB.get_instance().get_collection('Links')
            
            # Always update the updated_at timestamp
            validated_data['updated_at'] = datetime.now()
            
            # Log operation details
            Logger.debug_user_action(
                bleoidPartner1,
                f"Updating link: current partner={current_bleoidPartner2}, new partner={new_bleoidPartner2}",
                LogType.INFO.value,
                200
            )
            
            # STEP 1: Update the current link
            result1 = db.update_one(
                {"BLEOIdPartner1": bleoidPartner1},
                {"$set": validated_data}
            )
            
            # STEP 2: If we're linking to a new partner, update their link too
            if new_bleoidPartner2 is not None:
                # Update the other user's link to point back
                result2 = db.update_one(
                    {"BLEOIdPartner1": new_bleoidPartner2},
                    {"$set": {"BLEOIdPartner2": bleoidPartner1, "updated_at": datetime.now()}}
                )
                if result2.modified_count == 0:
                    # Log warning
                    Logger.debug_error(
                        f"Could not update reciprocal link for BLEOIdPartner1={new_bleoidPartner2}",
                        200,
                        bleoidPartner1,
                        ErrorSourceType.SERVER.value
                    )
                    
                    print(f"Warning: Could not update reciprocal link for BLEOIdPartner1={new_bleoidPartner2}")
            
            # STEP 3: If we previously had a partner, update their link to remove us
            if current_bleoidPartner2 is not None and current_bleoidPartner2 != new_bleoidPartner2:
                # Previous partner exists and it's different from the new one
                # We need to remove the link from the previous partner back to us
                result3 = db.update_one(
                    {"BLEOIdPartner1": current_bleoidPartner2},
                    {"$set": {"BLEOIdPartner2": None, "updated_at": datetime.now()}}
                )
                if result3.modified_count == 0:
                    # Log warning
                    Logger.debug_error(
                        f"Could not update previous partner's link for BLEOIdPartner1={current_bleoidPartner2}",
                        200,
                        bleoidPartner1,
                        ErrorSourceType.SERVER.value
                    )
                    
                    print(f"Warning: Could not update previous partner's link for BLEOIdPartner1={current_bleoidPartner2}")
            
            if result1.modified_count == 0:
                # Log no changes
                Logger.debug_user_action(
                    bleoidPartner1,
                    "No changes made to link",
                    LogType.INFO.value,
                    200
                )
                
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get and return updated link
            updated_link = self.get_object(bleoidPartner1)
            updated_link['_id'] = str(updated_link['_id'])
            
            # Serialize the response
            response_serializer = LinkSerializer(updated_link)
            
            # Log success
            Logger.debug_user_action(
                bleoidPartner1,
                f"Link updated successfully with partner {updated_link.get('BLEOIdPartner2')}",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Link updated successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to update link for BLEOIdPartner1={bleoidPartner1}: {str(e)}",
                500,
                bleoidPartner1,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to update link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoidPartner1):
        """Delete a link by BLEOIdPartner1"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting link for BLEOIdPartner1={bleoidPartner1}",
                LogType.INFO.value,
                200
            )
            
            # Check if link exists
            link = self.get_object(bleoidPartner1)
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOIdPartner1={bleoidPartner1} during deletion",
                    404,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current BLEOIdPartner2 value (to handle unlinking case)
            bleoidPartner2 = link.get('BLEOIdPartner2')
            
            # Delete by BLEOIdPartner1
            db = MongoDB.get_instance().get_collection('Links')
            result = db.delete_one({"BLEOIdPartner1": bleoidPartner1})
            
            # If this link had a partner, update their link too
            if bleoidPartner2:
                # Log operation
                Logger.debug_system_action(
                    f"Updating partner link for BLEOIdPartner1={bleoidPartner2}",
                    LogType.INFO.value,
                    200
                )
                
                update_result = db.update_one(
                    {"BLEOIdPartner1": bleoidPartner2},
                    {"$set": {"BLEOIdPartner2": None, "updated_at": datetime.now()}}
                )
                
                if update_result.modified_count > 0:
                    Logger.debug_system_action(
                        f"Successfully removed partner reference from BLEOIdPartner1={bleoidPartner2}",
                        LogType.SUCCESS.value,
                        200
                    )
            
            # Log success
            Logger.debug_user_action(
                bleoidPartner1,
                f"Link deleted successfully" + (f" (was linked to {bleoidPartner2})" if bleoidPartner2 else ""),
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                message="Link deleted successfully"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to delete link for BLEOIdPartner1={bleoidPartner1}: {str(e)}",
                500,
                bleoidPartner1,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)