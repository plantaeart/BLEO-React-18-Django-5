from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from api.Views.Link.LinkView import LinkListCreateView, LinkDetailView
from api.Views.User.UserView import UserListCreateView, UserDetailView
from models.Link import Link
from models.User import User
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
import time
import random
from datetime import datetime
from django.urls import path
from django.test import override_settings
from models.enums.ConnectionStatusType import ConnectionStatusType
from models.response.BLEOResponse import BLEOResponse

# Set up URL configuration for testing
urlpatterns = [
    path('links/', LinkListCreateView.as_view(), name='link-list'),
    path('links/<str:bleoidPartner1>/', LinkDetailView.as_view(), name='link-detail'),
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<str:bleoid>/', UserDetailView.as_view(), name='user-detail'),
]

@override_settings(ROOT_URLCONF=__name__)
class LinkViewTest(BLEOBaseTest):
    """Test cases for LinkListCreateView and LinkDetailView with MongoDB test collection"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        super().setUpClass()
        # Create MongoDB connection with test collections
        cls.db_client = MongoDB.get_client()
        
        # Use test collections with timestamp to avoid conflicts
        timestamp = int(time.time())
        cls.test_suffix = f"test_{timestamp}_{random.randint(1000, 9999)}"
        cls.links_collection_name = f"Links_{cls.test_suffix}"
        cls.users_collection_name = f"Users_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_links_collection = MongoDB.COLLECTIONS['Links']
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Links'] = cls.links_collection_name
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        
        print(f"🔧 Created test collections: {cls.links_collection_name}, {cls.users_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.links_collection_name)
            db.drop_collection(cls.users_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Links'] = cls.original_links_collection
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            
            print(f"🧹 Dropped test collections: {cls.links_collection_name}, {cls.users_collection_name}")
        except Exception as e:
            print(f"❌ Error during teardown: {str(e)}")
        finally:
            super().tearDownClass()
    
    def setUp(self):
        """Set up the test environment before each test"""
        super().setUp()
        # Use APIClient for testing
        self.client = APIClient()
        
        try:
            # Get test collections
            self.db_links = MongoDB.get_instance().get_collection('Links')
            self.db_users = MongoDB.get_instance().get_collection('Users')
            
            # Clear collections before each test
            self.db_links.delete_many({})
            self.db_users.delete_many({})
            
            # Create sample test users
            self.test_users = [
                {
                    'BLEOId': 'USER1',
                    'email': 'user1@example.com',
                    'password': make_password('Password123'),
                    'userName': 'TestUser1',
                    'created_at': datetime.now()
                },
                {
                    'BLEOId': 'USER2',
                    'email': 'user2@example.com',
                    'password': make_password('Password345'),
                    'userName': 'TestUser2',
                    'created_at': datetime.now()
                },
                {
                    'BLEOId': 'USER3',
                    'email': 'user3@example.com',
                    'password': make_password('Password567'),
                    'userName': 'TestUser3',
                    'created_at': datetime.now()
                },
                {
                    'BLEOId': 'USER4',
                    'email': 'user4@example.com',
                    'password': make_password('Password8910'),
                    'userName': 'TestUser4',
                    'created_at': datetime.now()
                }
            ]
            
            # Insert test users
            self.user_ids = []
            for i, user in enumerate(self.test_users):
                result = self.db_users.insert_one(user)
                self.user_ids.append(result.inserted_id)
                print(f"  ✅ Created test user {i+1}: {user['BLEOId']}")
            
            # Create sample test links
            now = datetime.now()
            self.test_links = [
                {
                    'BLEOIdPartner1': 'USER1',
                    'BLEOIdPartner2': 'USER2',
                    'status': ConnectionStatusType.ACCEPTED.value,
                    'created_at': now,
                    'updated_at': now
                },
                {
                    'BLEOIdPartner1': 'USER3',
                    'BLEOIdPartner2': 'USER4',
                    'status': ConnectionStatusType.PENDING.value,
                    'created_at': now,
                    'updated_at': now
                }
            ]
            
            # Insert test links
            self.link_ids = []
            for i, link in enumerate(self.test_links):
                result = self.db_links.insert_one(link)
                self.link_ids.append(result.inserted_id)
                print(f"  ✅ Created test link {i+1}: {link['BLEOIdPartner1']} -> {link['BLEOIdPartner2']}")
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} users and {len(self.link_ids)} links")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_links.delete_many({})
        self.db_users.delete_many({})
        super().tearDown()
    
    # ====== LinkListCreateView Tests ======
    
    def test_get_all_links(self):
        """Test getting all links"""
        # Make request
        response = self.client.get('/links/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['BLEOIdPartner1'], 'USER1')
        self.assertEqual(response.data['data'][1]['BLEOIdPartner1'], 'USER3')
        self.assertEqual(response.data['successMessage'], 'Links retrieved successfully')
        
        print("  🔹 Successfully retrieved all links")
    
    def test_create_link_success(self):
        """Test creating a new link successfully"""
        # Create a new user for this test
        new_user = {
            'BLEOId': 'USER5',
            'email': 'user5@example.com',
            'password': make_password('Password268'),
            'userName': 'TestUser5',
            'created_at': datetime.now()
        }
        self.db_users.insert_one(new_user)
        
        new_partner = {
            'BLEOId': 'USER6',
            'email': 'user6@example.com',
            'password': make_password('Password0985'),
            'userName': 'TestUser6',
            'created_at': datetime.now()
        }
        self.db_users.insert_one(new_partner)
        
        # Request data
        link_data = {
            'BLEOIdPartner1': 'USER5',
            'BLEOIdPartner2': 'USER6',
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['BLEOIdPartner1'], 'USER5')
        self.assertEqual(response.data['data']['BLEOIdPartner2'], 'USER6')
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.PENDING.value)
        
        print(f"  🔹 Successfully created link for USER5 with partner USER6")
    
    def test_create_link_with_partner(self):
        """Test creating a link with partner reference"""
        # First create a new user for this test
        new_user = {
            'BLEOId': 'USER5',
            'email': 'user5@example.com',
            'password': make_password('Password123'),
            'userName': 'TestUser5',
            'created_at': datetime.now()
        }
        self.db_users.insert_one(new_user)
        
        # Request data
        link_data = {
            'BLEOIdPartner1': 'USER5',
            'BLEOIdPartner2': 'USER3',  # USER3 exists and has no partner yet
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['BLEOIdPartner1'], 'USER5')
        self.assertEqual(response.data['data']['BLEOIdPartner2'], 'USER3')
        self.assertEqual(response.data['successMessage'], 'Link created successfully')
        
        print(f"  🔹 Successfully created link for USER5 with partner USER3")
    
    def test_create_link_duplicate(self):
        """Test error when creating duplicate link"""
        # Request data with existing BLEOIdPartner1
        link_data = {
            'BLEOIdPartner1': 'USER1',  # USER1 already has a link
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['errorType'], 'DuplicateError')
        self.assertEqual(response.data['errorMessage'], 'Link with BLEOIdPartner1=USER1 already exists')
        
        print("  🔹 Properly rejected duplicate link")
    
    def test_create_link_nonexistent_user(self):
        """Test error when creating a link for a nonexistent user"""
        # Request data with nonexistent user
        link_data = {
            'BLEOIdPartner1': 'NONEXISTENT',
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'User with BLEOId NONEXISTENT not found')
        
        print("  🔹 Properly rejected link for nonexistent user")
    
    def test_create_link_nonexistent_partner(self):
        """Test error when creating a link with nonexistent partner"""
        # Request data with nonexistent partner
        link_data = {
            'BLEOIdPartner1': 'USER3',  # USER3 exists
            'BLEOIdPartner2': 'NONEXISTENT',  # But this partner doesn't
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'User with BLEOId NONEXISTENT not found')
        
        print("  🔹 Properly rejected link with nonexistent partner")
    
    def test_create_link_invalid_data(self):
        """Test error when creating a link with invalid data"""
        # Request data missing required BLEOIdPartner1
        link_data = {
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request
        response = self.client.post('/links/', link_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('BLEOIdPartner1', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid data (missing BLEOIdPartner1)")
    
    # ====== LinkDetailView Tests ======
    
    def test_get_link_by_bleoidPartner1(self):
        """Test getting a link by BLEOIdPartner1"""
        # Make request
        response = self.client.get('/links/USER1/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['BLEOIdPartner1'], 'USER1')
        self.assertEqual(response.data['data']['BLEOIdPartner2'], 'USER2')
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.ACCEPTED.value)
        self.assertEqual(response.data['successMessage'], 'Link retrieved successfully')
        
        print("  🔹 Successfully retrieved link by BLEOIdPartner1")
    
    def test_get_nonexistent_link(self):
        """Test error when getting a nonexistent link"""
        # Make request with nonexistent BLEOIdPartner1
        response = self.client.get('/links/NONEXISTENT/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'No link found for BLEOIdPartner1=NONEXISTENT')
        
        print("  🔹 Properly handled nonexistent link")
    
    def test_update_link_success(self):
        """Test updating a link successfully"""
        # Update data
        update_data = {
            'status': ConnectionStatusType.BLOCKED.value  # Change status to blocked
        }
        
        # Make request
        response = self.client.put('/links/USER1/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['BLEOIdPartner1'], 'USER1')
        self.assertEqual(response.data['data']['BLEOIdPartner2'], 'USER2')
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.BLOCKED.value)
        self.assertEqual(response.data['successMessage'], 'Link updated successfully')
        
        # Verify changes in database
        updated_link = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertEqual(updated_link['status'], ConnectionStatusType.BLOCKED.value)
        
        print("  🔹 Successfully updated link status")
    
    def test_update_link_change_partner(self):
        """Test changing a partner by deleting the old link and creating a new one"""
        # First verify initial state
        initial_link1 = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertEqual(initial_link1['BLEOIdPartner2'], 'USER2')
        
        initial_link3 = self.db_links.find_one({'BLEOIdPartner1': 'USER3'})
        self.assertEqual(initial_link3['BLEOIdPartner2'], 'USER4')
        
        # First delete USER1's link with USER2
        delete_response = self.client.delete('/links/USER1/')
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify USER1's link was deleted
        deleted_link = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertIsNone(deleted_link)
        
        # Verify USER2's link is also deleted
        updated_link2 = self.db_links.find_one({'BLEOIdPartner1': 'USER2'})
        self.assertIsNone(updated_link2)
        
        # Now create a new link between USER1 and USER3
        new_link_data = {
            'BLEOIdPartner1': 'USER1',
            'BLEOIdPartner2': 'USER3',
            'status': ConnectionStatusType.PENDING.value
        }
        
        # Make request to create new link
        create_response = self.client.post('/links/', new_link_data, format='json')
        
        # Check response
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data['data']['BLEOIdPartner1'], 'USER1')
        self.assertEqual(create_response.data['data']['BLEOIdPartner2'], 'USER3')
        
        # Verify in database that USER1 now has a link to USER3
        new_link1 = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertIsNotNone(new_link1)
        self.assertEqual(new_link1['BLEOIdPartner2'], 'USER3')
        
        # Verify USER3's status - should still have the link with USER4
        user3_link = self.db_links.find_one({'BLEOIdPartner1': 'USER3'})
        self.assertIsNotNone(user3_link)
        
        print("  🔹 Successfully changed partner by deleting and recreating link")
    
    def test_update_link_nonexistent(self):
        """Test error when updating a nonexistent link"""
        # Update data
        update_data = {
            'status': ConnectionStatusType.ACCEPTED.value
        }
        
        # Make request with nonexistent BLEOIdPartner1
        response = self.client.put('/links/NONEXISTENT/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'No link found for BLEOIdPartner1=NONEXISTENT')
        
        print("  🔹 Properly handled update for nonexistent link")
    
    def test_update_link_invalid_data(self):
        """Test error when updating a link with invalid data"""
        # Update data with invalid status
        update_data = {
            'status': 'invalid_status'
        }
        
        # Make request
        response = self.client.put('/links/USER1/', update_data, format='json')
        
        # Check response - FIX: using response.data instead of response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('status', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid update data")
    
    def test_delete_link_success(self):
        """Test deleting a link successfully"""
        # Make request
        response = self.client.delete('/links/USER3/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Link deleted successfully')
        
        # Verify link was deleted from database
        link = self.db_links.find_one({'BLEOIdPartner1': 'USER3'})
        self.assertIsNone(link)
        
        # Verify partner's link is also deleted
        link4 = self.db_links.find_one({'BLEOIdPartner1': 'USER4'})
        self.assertIsNone(link4)
        
        print("  🔹 Successfully deleted link for both partners")
    
    def test_delete_link_with_partner(self):
        """Test deleting a link that has a partner"""
        # Make request
        response = self.client.delete('/links/USER1/')  # USER1 is linked to USER2
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Link deleted successfully')
        
        # Verify link was deleted from database for both users
        link1 = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertIsNone(link1)
        
        # Partner's link should also be deleted
        link2 = self.db_links.find_one({'BLEOIdPartner1': 'USER2'})
        self.assertIsNone(link2)
        
        print("  🔹 Successfully deleted link for both partners")
    
    def test_delete_nonexistent_link(self):
        """Test error when deleting a nonexistent link"""
        # Make request with nonexistent BLEOIdPartner1
        response = self.client.delete('/links/NONEXISTENT/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'No link found for BLEOIdPartner1=NONEXISTENT')
        
        print("  🔹 Properly handled delete for nonexistent link")
    
    def test_links_removed_when_user_deleted(self):
        """Test that links are deleted when a user is deleted"""
        # Create a user API client
        user_client = APIClient()
        
        # First verify our links exist
        link1 = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertIsNotNone(link1)
        self.assertEqual(link1['BLEOIdPartner2'], 'USER2')
        
        link3 = self.db_links.find_one({'BLEOIdPartner1': 'USER3'})
        self.assertIsNotNone(link3)
        self.assertEqual(link3['BLEOIdPartner2'], 'USER4')
        
        # Delete USER1 through the User API
        user_delete_response = user_client.delete('/users/USER1/')
        self.assertEqual(user_delete_response.status_code, 200)
        
        # Verify that USER1's link has been deleted
        deleted_link1 = self.db_links.find_one({'BLEOIdPartner1': 'USER1'})
        self.assertIsNone(deleted_link1)
        
        # Verify that USER2's link has been deleted too
        user2_link = self.db_links.find_one({'BLEOIdPartner1': 'USER2'})
        self.assertIsNone(user2_link)
        
        # Now delete USER3
        user_delete_response = user_client.delete('/users/USER3/')
        self.assertEqual(user_delete_response.status_code, 200)
        
        # Verify that USER3's link has been deleted
        deleted_link3 = self.db_links.find_one({'BLEOIdPartner1': 'USER3'})
        self.assertIsNone(deleted_link3)
        
        # Verify that USER4's link has been deleted too
        user4_link = self.db_links.find_one({'BLEOIdPartner1': 'USER4'})
        self.assertIsNone(user4_link)
        
        print("  🔹 Successfully verified links are deleted when users are deleted")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(LinkViewTest)