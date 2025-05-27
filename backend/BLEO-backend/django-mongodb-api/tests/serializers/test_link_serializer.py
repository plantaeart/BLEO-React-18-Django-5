from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import LinkSerializer
from datetime import datetime

class LinkSerializerTest(BLEOBaseTest):
    """Test cases for LinkSerializer validation and transformation"""
    
    def test_valid_link_data(self):
        """Test that valid link data passes validation"""
        data = {
            'BLEOIdPartner1': 'WQJ94S',
            'BLEOIdPartner2': 'ABC123', 
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['BLEOIdPartner1'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['BLEOIdPartner2'], 'ABC123')
        print(f"  🔹 Validated BLEOIdPartner1: {serializer.validated_data['BLEOIdPartner1']}")
        print(f"  🔹 Validated BLEOIdPartner2: {serializer.validated_data['BLEOIdPartner2']}")
        print(f"  🔹 Validated status: {serializer.validated_data['status']}")
    
    def test_null_partner2(self):
        """Test that null BLEOIdPartner2 is allowed"""
        data = {
            'BLEOIdPartner1': 'WQJ94S',
            'BLEOIdPartner2': None,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data['BLEOIdPartner2'])
        print(f"  🔹 Validated BLEOIdPartner1: {serializer.validated_data['BLEOIdPartner1']}")
        print(f"  🔹 Confirmed BLEOIdPartner2 is None")
    
    def test_invalid_status(self):
        """Test that invalid status values are rejected"""
        data = {
            'BLEOIdPartner1': 'WQJ94S',
            'BLEOIdPartner2': 'ABC123',
            'status': 'invalid_status',  # Invalid status
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        print(f"  🔹 Status error detected: {serializer.errors.get('status')}")
    
    def test_missing_partner1(self):
        """Test that missing BLEOIdPartner1 is rejected"""
        data = {
            'BLEOIdPartner2': 'ABC123',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('BLEOIdPartner1', serializer.errors)
        print(f"  🔹 Missing BLEOIdPartner1 error detected: {serializer.errors.get('BLEOIdPartner1')}")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(LinkSerializerTest)