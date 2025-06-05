from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import LinkSerializer
from datetime import datetime

class LinkSerializerTest(BLEOBaseTest):
    """Test cases for LinkSerializer validation and transformation"""
    
    def test_valid_link_data(self):
        """Test that valid link data passes validation"""
        data = {
            'bleoidPartner1': 'WQJ94S',
            'bleoidPartner2': 'ABC123', 
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bleoidPartner1'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['bleoidPartner2'], 'ABC123')
        print(f"  🔹 Validated bleoidPartner1: {serializer.validated_data['bleoidPartner1']}")
        print(f"  🔹 Validated bleoidPartner2: {serializer.validated_data['bleoidPartner2']}")
        print(f"  🔹 Validated status: {serializer.validated_data['status']}")
    
    def test_null_partner2(self):
        """Test that null bleoidPartner2 is rejected"""
        data = {
            'bleoidPartner1': 'WQJ94S',
            'bleoidPartner2': None,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        
        # Fix: Now we expect this to be invalid
        self.assertFalse(serializer.is_valid())
        self.assertIn('bleoidPartner2', serializer.errors)
        
        # Check the error message
        error_message = str(serializer.errors['bleoidPartner2'])
        self.assertIn('this field may not be null.', error_message.lower())
        
        print(f"  🔹 Correctly rejected null bleoidPartner2")
        print(f"  🔹 Error message: {serializer.errors['bleoidPartner2']}")
    
    def test_invalid_status(self):
        """Test that invalid status values are rejected"""
        data = {
            'bleoidPartner1': 'WQJ94S',
            'bleoidPartner2': 'ABC123',
            'status': 'invalid_status',  # Invalid status
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        print(f"  🔹 Status error detected: {serializer.errors.get('status')}")
    
    def test_missing_partner1(self):
        """Test that missing bleoidPartner1 is rejected"""
        data = {
            'bleoidPartner2': 'ABC123',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        serializer = LinkSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bleoidPartner1', serializer.errors)
        print(f"  🔹 Missing bleoidPartner1 error detected: {serializer.errors.get('bleoidPartner1')}")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(LinkSerializerTest)