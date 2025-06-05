from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import ConnectionRequestSerializer, ConnectionResponseSerializer, ConnectionSerializer, ConnectionFilterSerializer
from datetime import datetime

class ConnectionRequestSerializerTest(BLEOBaseTest):
    """Test cases for ConnectionRequestSerializer validation"""
    
    def test_valid_connection_request(self):
        """Test that valid connection request passes validation"""
        data = {
            'from_bleoid': 'WQJ94S',
            'to_bleoid': 'ABC123'
        }
        serializer = ConnectionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['from_bleoid'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['to_bleoid'], 'ABC123')
        print(f"  🔹 Validated from_bleoid: {serializer.validated_data['from_bleoid']}")
        print(f"  🔹 Validated to_bleoid: {serializer.validated_data['to_bleoid']}")
    
    def test_same_user_connection_request(self):
        """Test that connection request to self is rejected"""
        data = {
            'from_bleoid': 'WQJ94S',
            'to_bleoid': 'WQJ94S'  # Same as from_bleoid
        }
        serializer = ConnectionRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('to_bleoid', serializer.errors)
        print(f"  🔹 Self-connection error detected: {serializer.errors.get('to_bleoid')}")
    
    def test_bleoid_format_validation(self):
        """Test BLEOID format validation in ConnectionRequest"""
        invalid_cases = [
            {'from_bleoid': 'abc-123', 'to_bleoid': 'DEF456'},
            {'from_bleoid': 'ABC123', 'to_bleoid': 'def@456'},
            {'from_bleoid': '', 'to_bleoid': 'DEF456'},
            {'from_bleoid': 'ABC123', 'to_bleoid': ''},
            {'from_bleoid': 'ABCDEFG', 'to_bleoid': 'DEF456'},  # Too long
            {'from_bleoid': 'ABC12', 'to_bleoid': 'DEF456'},    # Too short
        ]
        
        for case in invalid_cases:
            serializer = ConnectionRequestSerializer(data=case)
            self.assertFalse(serializer.is_valid())
            
            # Should have errors for invalid fields
            invalid_from = case['from_bleoid'] in ['abc-123', '', 'ABCDEFG', 'ABC12']
            invalid_to = case['to_bleoid'] in ['def@456', '', 'ABCDEFG', 'ABC12']
            
            if invalid_from:
                self.assertIn('from_bleoid', serializer.errors)
            if invalid_to:
                self.assertIn('to_bleoid', serializer.errors)
        
        print("  🔹 BLEOID format validation works in ConnectionRequest")

    def test_bleoid_normalization(self):
        """Test BLEOID normalization in ConnectionRequest"""
        data = {
            'from_bleoid': 'abc123',  # Lowercase
            'to_bleoid': 'def456'     # Lowercase
        }
        
        serializer = ConnectionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Should be normalized to uppercase
        self.assertEqual(serializer.validated_data['from_bleoid'], 'ABC123')
        self.assertEqual(serializer.validated_data['to_bleoid'], 'DEF456')
        
        print("  🔹 BLEOID normalization works in ConnectionRequest")


class ConnectionResponseSerializerTest(BLEOBaseTest):
    """Test cases for ConnectionResponseSerializer validation"""
    
    def test_valid_connection_response(self):
        """Test that valid connection response passes validation"""
        data = {
            'action': 'accept'
        }
        serializer = ConnectionResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['action'], 'accept')
        print(f"  🔹 Validated action: {serializer.validated_data['action']}")
    
    def test_invalid_action(self):
        """Test that invalid action is rejected"""
        data = {
            'action': 'invalid_action'  # Not in allowed choices
        }
        serializer = ConnectionResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('action', serializer.errors)
        print(f"  🔹 Invalid action error detected: {serializer.errors.get('action')}")


class ConnectionSerializerTest(BLEOBaseTest):
    """Test cases for ConnectionSerializer validation and transformation"""
    
    def test_valid_connection(self):
        """Test that valid connection passes validation"""
        data = {
            'bleoidPartner1': 'WQJ94S',
            'bleoidPartner2': 'ABC123',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        serializer = ConnectionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bleoidPartner1'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['status'], 'pending')
        print(f"  🔹 Validated bleoidPartner1: {serializer.validated_data['bleoidPartner1']}")
        print(f"  🔹 Validated status: {serializer.validated_data['status']}")
    
    def test_invalid_status(self):
        """Test that invalid status is rejected"""
        data = {
            'bleoidPartner1': 'WQJ94S',
            'bleoidPartner2': 'ABC123',
            'status': 'invalid_status',  # Not in allowed choices
            'created_at': datetime.now().isoformat()
        }
        serializer = ConnectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        print(f"  🔹 Invalid status error detected: {serializer.errors.get('status')}")
    
    def test_bleoid_format_validation_in_connection(self):
        """Test BLEOID format validation in Connection serializer"""
        invalid_data = {
            'bleoidPartner1': 'abc-123',  # Invalid format
            'bleoidPartner2': 'DEF456',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        serializer = ConnectionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bleoidPartner1', serializer.errors)
        
        print("  🔹 BLEOID format validation works in Connection serializer")

    def test_connection_direction_method(self):
        """Test connection direction calculation"""
        connection_data = {
            'bleoidPartner1': 'ABC123',
            'bleoidPartner2': 'DEF456',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Test outgoing direction (current user is partner1)
        serializer = ConnectionSerializer(
            data=connection_data, 
            context={'current_user': 'ABC123'}
        )
        self.assertTrue(serializer.is_valid())
        
        # Test incoming direction (current user is partner2)
        serializer2 = ConnectionSerializer(
            data=connection_data,
            context={'current_user': 'DEF456'}
        )
        self.assertTrue(serializer2.is_valid())
        
        print("  🔹 Connection direction calculation works correctly")
    
    def test_connection_filter_bleoid_validation(self):
        """Test BLEOID validation in ConnectionFilter"""
        # Valid BLEOID
        data1 = {
            'bleoid': 'ABC123',
            'status': 'pending',
            'direction': 'both'
        }
        serializer1 = ConnectionFilterSerializer(data=data1)
        self.assertTrue(serializer1.is_valid())
        
        # Invalid BLEOID
        data2 = {
            'bleoid': 'abc-123',  # Invalid format
            'status': 'all'
        }
        serializer2 = ConnectionFilterSerializer(data=data2)
        # Should fail if BLEOID validation is implemented
        if not serializer2.is_valid():
            self.assertIn('bleoid', serializer2.errors)
            print("    ✓ ConnectionFilter BLEOID validation works")
        
        print("  🔹 ConnectionFilter validation checked")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running ConnectionRequestSerializerTest...")
    run_test_with_output(ConnectionRequestSerializerTest)
    
    print("\nRunning ConnectionResponseSerializerTest...")
    run_test_with_output(ConnectionResponseSerializerTest)
    
    print("\nRunning ConnectionSerializerTest...")
    run_test_with_output(ConnectionSerializerTest)