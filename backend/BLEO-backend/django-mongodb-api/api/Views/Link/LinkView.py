from rest_framework.views import APIView
from rest_framework import status
from models.Link import Link
from utils.mongodb_utils import MongoDB
from bson import ObjectId
from datetime import datetime
from models.response.BLEOResponse import BLEOResponse

class LinkListCreateView(APIView):
    """API view for listing and creating links"""
    
    def get(self, request):
        """Get all links"""
        try:
            db = MongoDB.get_instance().get_collection('Links')
            links = list(db.find({}))
            
            # Convert ObjectId to string for JSON serialization
            for link in links:
                link['_id'] = str(link['_id'])
                if 'created_at' in link:
                    # Format as DD:MM:YYYY
                    link['created_at'] = link['created_at'].strftime('%d:%m:%Y')
                
            return BLEOResponse.success(
                data=links,
                message="Links retrieved successfully"
            ).to_response()
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve links: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new link with BLEOIdPartner1 required, BLEOIdPartner2 optional"""
        try:
            data = request.data
            
            # Validate BLEOIdPartner1 is provided (required)
            if 'BLEOIdPartner1' not in data:
                return BLEOResponse.validation_error(
                    message="Missing required field: BLEOIdPartner1"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Convert BLEOIdPartner1 to integer
            try:
                bleoidPartner1 = int(data['BLEOIdPartner1'])
            except (ValueError, TypeError):
                return BLEOResponse.validation_error(
                    message="BLEOIdPartner1 must be a number"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check if BLEOIdPartner1 user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user1 = db_users.find_one({"BLEOId": bleoidPartner1})
            
            if not user1:
                return BLEOResponse.not_found(
                    message=f"User with BLEOId {bleoidPartner1} not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Process BLEOIdPartner2 if provided
            bleoidPartner2 = None
            if 'BLEOIdPartner2' in data and data['BLEOIdPartner2'] is not None:
                try:
                    bleoidPartner2 = int(data['BLEOIdPartner2'])
                    
                    # Check if BLEOIds are the same
                    if bleoidPartner1 == bleoidPartner2:
                        return BLEOResponse.validation_error(
                            message="Cannot link a user to themselves"
                        ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                    # Check if BLEOIdPartner2 user exists
                    user2 = db_users.find_one({"BLEOId": bleoidPartner2})
                    if not user2:
                        return BLEOResponse.not_found(
                            message=f"User with BLEOId {bleoidPartner2} not found"
                        ).to_response(status.HTTP_404_NOT_FOUND)
                except (ValueError, TypeError):
                    return BLEOResponse.validation_error(
                        message="BLEOIdPartner2 must be a number"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Check if link already exists with this BLEOIdPartner1
            db_links = MongoDB.get_instance().get_collection('Links')
            existing_link = db_links.find_one({"BLEOIdPartner1": bleoidPartner1})
            
            if existing_link:
                return BLEOResponse.error(
                    error_type="DuplicateError",
                    error_message=f"Link with BLEOIdPartner1={bleoidPartner1} already exists"
                ).to_response(status.HTTP_409_CONFLICT)
            
            # If created_at is provided as a string
            if 'created_at' in data and isinstance(data['created_at'], str):
                try:
                    # Parse DD:MM:YYYY format
                    created_at = datetime.strptime(data['created_at'], '%d-%m-%Y')
                except ValueError:
                    return BLEOResponse.validation_error(
                        message="Invalid date format, use DD-MM-YYYY"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
            else:
                created_at = datetime.now()
            
            # Create link with parsed datetime
            link = Link(
                BLEOIdPartner1=bleoidPartner1,
                BLEOIdPartner2=bleoidPartner2,  # Can be None
                created_at=created_at
            )
            
            # Save to MongoDB
            result = db_links.insert_one(link.to_dict())
            
            # Return created link with ID
            created_link = link.to_dict()
            created_link['_id'] = str(result.inserted_id)
            
            return BLEOResponse.success(
                data=created_link,
                message="Link created successfully"
            ).to_response(status.HTTP_201_CREATED)
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to create link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)


class LinkDetailView(APIView):
    """API view for getting, updating and deleting a link"""
    
    def get_object(self, bleoidPartner1):
        """Get a single link by BLEOIdPartner1"""
        try:
            bleoidPartner1 = int(bleoidPartner1)
            db = MongoDB.get_instance().get_collection('Links')
            return db.find_one({"BLEOIdPartner1": bleoidPartner1})
        except (ValueError, TypeError):
            return None
    
    def get(self, request, bleoidPartner1):
        """Get a link by BLEOIdPartner1"""
        try:
            # Convert to integer for lookup
            try:
                bleoidPartner1Value = int(bleoidPartner1)
            except ValueError:
                return BLEOResponse.validation_error(
                    message="Invalid BLEOIdPartner1 format, must be a number"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get link by BLEOIdPartner1
            link = self.get_object(bleoidPartner1Value)
            
            if link is None:
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1Value}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Convert ObjectId to string for JSON serialization
            link['_id'] = str(link['_id'])
            if 'created_at' in link:
                # Format as DD:MM:YYYY
                link['created_at'] = link['created_at'].strftime('%d:%m:%Y')
            
            return BLEOResponse.success(
                data=link,
                message="Link retrieved successfully"
            ).to_response()
                
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to retrieve link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)           
    
    def put(self, request, bleoidPartner1):
        """Update BLEOIdPartner2 for a link and automatically update the reciprocal link"""
        try:
            # Convert to integer for lookup
            try:
                bleoidPartner1Value = int(bleoidPartner1)
            except ValueError:
                return BLEOResponse.validation_error(
                    message="Invalid BLEOIdPartner1 format, must be a number"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get the link
            db = MongoDB.get_instance().get_collection('Links')
            link = self.get_object(bleoidPartner1Value)
            
            if link is None:
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1Value}"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Get current BLEOIdPartner2 value (to handle unlinking case)
            current_bleoidPartner2 = link.get('BLEOIdPartner2')
            
            # Process updated BLEOIdPartner2
            data = request.data
            new_bleoidPartner2 = None
            
            if 'BLEOIdPartner2' in data and data['BLEOIdPartner2'] is not None:
                try:
                    new_bleoidPartner2 = int(data['BLEOIdPartner2'])
                    
                    # Check if BLEOIds are the same
                    if bleoidPartner1Value == new_bleoidPartner2:
                        return BLEOResponse.validation_error(
                            message="Cannot link a user to themselves"
                        ).to_response(status.HTTP_400_BAD_REQUEST)
                    
                    # Check if BLEOIdPartner2 user exists
                    db_users = MongoDB.get_instance().get_collection('Users')
                    user2 = db_users.find_one({"BLEOId": new_bleoidPartner2})
                    if not user2:
                        return BLEOResponse.not_found(
                            message=f"User with BLEOId {new_bleoidPartner2} not found"
                        ).to_response(status.HTTP_404_NOT_FOUND)
                        
                    # Check if the target user has a link
                    partner2_link = db.find_one({"BLEOIdPartner1": new_bleoidPartner2})
                    if not partner2_link:
                        return BLEOResponse.not_found(
                            message=f"User with BLEOId {new_bleoidPartner2} does not have a link"
                        ).to_response(status.HTTP_404_NOT_FOUND)
                        
                except (ValueError, TypeError):
                    return BLEOResponse.validation_error(
                        message="BLEOIdPartner2 must be a number"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
        
            # STEP 1: Update the current link's BLEOIdPartner2
            result1 = db.update_one(
                {"BLEOIdPartner1": bleoidPartner1Value},
                {"$set": {"BLEOIdPartner2": new_bleoidPartner2}}  # Can be None to unlink
            )
            
            # STEP 2: If we're linking to a new partner, update their link too
            if new_bleoidPartner2 is not None:
                # Update the other user's link to point back
                result2 = db.update_one(
                    {"BLEOIdPartner1": new_bleoidPartner2},
                    {"$set": {"BLEOIdPartner2": bleoidPartner1Value}}
                )
                if result2.modified_count == 0:
                    print(f"Warning: Could not update reciprocal link for BLEOIdPartner1={new_bleoidPartner2}")
            
            # STEP 3: If we previously had a partner, update their link to remove us
            if current_bleoidPartner2 is not None and current_bleoidPartner2 != new_bleoidPartner2:
                # Previous partner exists and it's different from the new one
                # We need to remove the link from the previous partner back to us
                result3 = db.update_one(
                    {"BLEOIdPartner1": current_bleoidPartner2},
                    {"$set": {"BLEOIdPartner2": None}}
                )
                if result3.modified_count == 0:
                    print(f"Warning: Could not update previous partner's link for BLEOIdPartner1={current_bleoidPartner2}")
            
            if result1.modified_count == 0:
                return BLEOResponse.success(
                    message="No changes made"
                ).to_response(status.HTTP_200_OK)
            
            # Get and return updated link
            updated_link = self.get_object(bleoidPartner1Value)
            updated_link['_id'] = str(updated_link['_id'])
            if 'created_at' in updated_link:
                updated_link['created_at'] = updated_link['created_at'].strftime('%d:%m:%Y')
            
            return BLEOResponse.success(
                data=updated_link,
                message="Link updated successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to update link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, bleoidPartner1):
        """Delete a link by BLEOIdPartner1"""
        try:
            # Convert to integer for lookup
            try:
                bleoidPartner1Value = int(bleoidPartner1)
            except ValueError:
                return BLEOResponse.validation_error(
                    message="Invalid BLEOIdPartner1 format, must be a number"
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            # Delete by BLEOIdPartner1
            db = MongoDB.get_instance().get_collection('Links')
            result = db.delete_one({"BLEOIdPartner1": bleoidPartner1Value})
            
            if result.deleted_count == 0:
                return BLEOResponse.not_found(
                    message=f"No link found for BLEOIdPartner1={bleoidPartner1Value}"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            return BLEOResponse.success(
                message="Link deleted successfully"
            ).to_response(status.HTTP_200_OK)  # Using 200 instead of 204 to include the success message
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to delete link: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)