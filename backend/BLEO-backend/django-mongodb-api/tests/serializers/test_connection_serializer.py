from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import ConnectionRequestSerializer, ConnectionResponseSerializer, ConnectionSerializer
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
            'BLEOIdPartner1': 'WQJ94S',
            'BLEOIdPartner2': 'ABC123',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        serializer = ConnectionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['BLEOIdPartner1'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['status'], 'pending')
        print(f"  🔹 Validated BLEOIdPartner1: {serializer.validated_data['BLEOIdPartner1']}")
        print(f"  🔹 Validated status: {serializer.validated_data['status']}")
    
    def test_invalid_status(self):
        """Test that invalid status is rejected"""
        data = {
            'BLEOIdPartner1': 'WQJ94S',
            'BLEOIdPartner2': 'ABC123',
            'status': 'invalid_status',  # Not in allowed choices
            'created_at': datetime.now().isoformat()
        }
        serializer = ConnectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        print(f"  🔹 Invalid status error detected: {serializer.errors.get('status')}")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running ConnectionRequestSerializerTest...")
    run_test_with_output(ConnectionRequestSerializerTest)
    
    print("\nRunning ConnectionResponseSerializerTest...")
    run_test_with_output(ConnectionResponseSerializerTest)
    
    print("\nRunning ConnectionSerializerTest...")
    run_test_with_output(ConnectionSerializerTest)