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
from utils.validation_utils import validate_url_bleoid
from rest_framework.exceptions import ValidationError

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
        """Create a new link with both partners required"""
        try:
            # Use serializer for validation
            serializer = LinkSerializer(data=request.data)
            if not serializer.is_valid():
                # Enhanced error logging for new required fields
                error_fields = ", ".join(serializer.errors.keys())
                
                # Check for specific partner validation errors
                partner_errors = []
                if 'bleoidPartner1' in serializer.errors:
                    partner_errors.append(f"Partner1: {serializer.errors['bleoidPartner1']}")
                if 'bleoidPartner2' in serializer.errors:
                    partner_errors.append(f"Partner2: {serializer.errors['bleoidPartner2']}")
                
                Logger.debug_error(
                    f"Link creation validation failed: {error_fields}",
                    400,
                    request.data.get('bleoidPartner1'),
                    ErrorSourceType.SERVER.value
                )
                
                error_message = "Link validation failed"
                if partner_errors:
                    error_message += f". Partner errors: {'; '.join(partner_errors)}"
                
                return BLEOResponse.validation_error(
                    message=error_message,
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            # Both partners are now guaranteed to be valid and non-null
            bleoidPartner1 = validated_data['bleoidPartner1']
            bleoidPartner2 = validated_data['bleoidPartner2']
            
            # Check if users exist
            db_users = MongoDB.get_instance().get_collection('Users')
            user1 = db_users.find_one({"bleoid": bleoidPartner1})
            
            if not user1:
                # Log user not found error
                Logger.debug_error(
                    f"User with bleoid {bleoidPartner1} not found when creating link",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"User with bleoid {bleoidPartner1} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            user2 = db_users.find_one({"bleoid": bleoidPartner2})
            if not user2:
                # Log second user not found error
                Logger.debug_error(
                    f"User with bleoid {bleoidPartner2} not found when creating link",
                    404,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"User with bleoid {bleoidPartner2} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Check if link already exists with this bleoidPartner1
            db_links = MongoDB.get_instance().get_collection('Links')
            existing_link = db_links.find_one({"bleoidPartner1": bleoidPartner1})
            
            if existing_link:
                # Log duplicate link error
                Logger.debug_error(
                    f"Link with bleoidPartner1={bleoidPartner1} already exists",
                    409,
                    bleoidPartner1,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Link with bleoidPartner1={bleoidPartner1} already exists"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # Create link
            link = Link(
                bleoidPartner1=bleoidPartner1,
                bleoidPartner2=bleoidPartner2,
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
            # Get bleoidPartner1 if available
            bleoidPartner1 = None
            try:
                bleoidPartner1 = request.data.get('bleoidPartner1')
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
    
    def get_object(self, bleoid):
        """Get a single link by BLEOID (searches both partner1 and partner2 fields)"""
        db = MongoDB.get_instance().get_collection('Links')
        return db.find_one({
            "$or": [
                {"bleoidPartner1": bleoid},
                {"bleoidPartner2": bleoid}
            ]
        })
    
    def get(self, request, bleoid):
        """Get a link by BLEOID (searches both partner1 and partner2 fields)"""
        try:
            # Validate BLEOID from URL parameter
            validated_bleoid = validate_url_bleoid(bleoid, "bleoid")
            
            # Find link where the BLEOID is either partner1 or partner2
            db = MongoDB.get_instance().get_collection('Links')
            link = db.find_one({
                "$or": [
                    {"bleoidPartner1": validated_bleoid},
                    {"bleoidPartner2": validated_bleoid}
                ]
            })
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOID={validated_bleoid}",
                    404,
                    validated_bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOID={validated_bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Convert ObjectId to string for JSON serialization
            link['_id'] = str(link['_id'])
            
            # Serialize the link
            serializer = LinkSerializer(link)
            
            # Log success
            Logger.debug_user_action(
                validated_bleoid,
                "Link retrieved successfully",
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                data=serializer.data,
                message="Link retrieved successfully"
            ).to_response()
                
        except ValidationError as e:
            Logger.debug_error(
                f"Invalid BLEOID format in URL: {str(e)}",
                400,
                None,
                ErrorSourceType.SERVER.value
            )
            return BLEOResponse.validation_error(
                message=f"Invalid BLEOID format in URL"
            ).to_response(status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to retrieve link for BLEOID={bleoid}: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to retrieve link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)           
    
    def put(self, request, bleoid):
        """Update a link"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Updating link for BLEOID={bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Get the link (this searches both partner fields)
            link = self.get_object(bleoid)
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOID={bleoid} during update",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOID={bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current partner values
            current_bleoidPartner1 = link.get('bleoidPartner1')
            current_bleoidPartner2 = link.get('bleoidPartner2')
            
            # Validate with serializer
            serializer = LinkSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                # Log validation error
                Logger.debug_error(
                    f"Link update validation failed: {serializer.errors}",
                    400,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            validated_data = serializer.validated_data
            
            # Don't allow changing partner BLEOIDs (they define the relationship)
            if 'bleoidPartner1' in validated_data:
                del validated_data['bleoidPartner1']
            if 'bleoidPartner2' in validated_data:
                del validated_data['bleoidPartner2']
            
            # Always update the updated_at timestamp
            validated_data['updated_at'] = datetime.now()
            
            # Update the link using the _id from the found record
            db = MongoDB.get_instance().get_collection('Links')
            result = db.update_one(
                {"_id": link["_id"]},
                {"$set": validated_data}
            )
            
            if result.modified_count == 0:
                # Log no changes
                Logger.debug_user_action(
                    bleoid,
                    "No changes made to link",
                    LogType.INFO.value,
                    200
                )
                
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get and return updated link
            updated_link = self.get_object(bleoid)
            updated_link['_id'] = str(updated_link['_id'])
            
            # Serialize the response
            response_serializer = LinkSerializer(updated_link)
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Link updated successfully (partners: {updated_link.get('bleoidPartner1')} <-> {updated_link.get('bleoidPartner2')})",
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
                f"Failed to update link for BLEOID={bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to update link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoid):
        """Delete a link by BLEOID (searches both partner1 and partner2 fields)"""
        try:
            # Log request
            Logger.debug_system_action(
                f"Deleting link for BLEOID={bleoid}",
                LogType.INFO.value,
                200
            )
            
            # Check if link exists (this already searches both partner fields)
            link = self.get_object(bleoid)
            
            if link is None:
                # Log not found error
                Logger.debug_error(
                    f"No link found for BLEOID={bleoid} during deletion",
                    404,
                    bleoid,  # ✅ Use bleoid
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOID={bleoid}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get both partner values (the record contains both)
            bleoidPartner1 = link.get('bleoidPartner1')
            bleoidPartner2 = link.get('bleoidPartner2')
            
            # Delete the single record (one record for both users)
            db = MongoDB.get_instance().get_collection('Links')
            result = db.delete_one({"_id": link["_id"]})
            
            # Log success
            Logger.debug_user_action(
                bleoid,  # ✅ Use bleoid
                f"Link deleted successfully (partners: {bleoidPartner1} <-> {bleoidPartner2})",
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                message="Link deleted successfully"
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Failed to delete link for BLEOID={bleoid}: {str(e)}",
                500,
                bleoid,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to delete link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)