import secrets
import os
import base64
import hashlib
from datetime import datetime
from pathlib import Path

class JWTSecretGenerator:
    """Utility class for generating and managing JWT secrets"""
    
    @staticmethod
    def generate_secure_secret(length=64):
        """
        Generate a cryptographically secure JWT secret
        
        Args:
            length (int): Length of the secret in bytes (default: 64)
            
        Returns:
            str: Base64 encoded secure secret
        """
        # Generate cryptographically secure random bytes
        secret_bytes = secrets.token_bytes(length)
        
        # Encode to base64 for easy storage
        secret_base64 = base64.b64encode(secret_bytes).decode('utf-8')
        
        return secret_base64
    
    @staticmethod
    def generate_secret_with_metadata():
        """
        Generate a JWT secret with metadata for tracking
        
        Returns:
            dict: Dictionary containing secret and metadata
        """
        secret = JWTSecretGenerator.generate_secure_secret()
        
        return {
            'secret': secret,
            'algorithm': 'HS256',
            'generated_at': datetime.now().isoformat(),
            'length_bytes': 64,
            'encoding': 'base64'
        }
    
    @staticmethod
    def generate_secret_from_passphrase(passphrase, salt=None):
        """
        Generate a deterministic JWT secret from a passphrase using PBKDF2
        
        Args:
            passphrase (str): The passphrase to derive secret from
            salt (str, optional): Salt for key derivation. If None, generates random salt
            
        Returns:
            dict: Dictionary containing secret, salt, and metadata
        """
        if salt is None:
            salt = secrets.token_hex(16)
        elif isinstance(salt, str):
            salt = salt.encode('utf-8')
        
        # Use PBKDF2 for key derivation
        secret_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            passphrase.encode('utf-8'),
            salt if isinstance(salt, bytes) else salt.encode('utf-8'),
            100000,  # 100,000 iterations
            64       # 64 bytes output
        )
        
        secret_base64 = base64.b64encode(secret_bytes).decode('utf-8')
        
        return {
            'secret': secret_base64,
            'salt': salt.hex() if isinstance(salt, bytes) else salt,
            'algorithm': 'HS256',
            'method': 'PBKDF2_HMAC_SHA256',
            'iterations': 100000,
            'generated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def save_secret_to_env(secret, env_file_path=None, backup_existing=True):
        """
        Save JWT secret to .env file without overriding existing content
        
        Args:
            secret (str): The JWT secret to save
            env_file_path (str, optional): Path to .env file. Defaults to project root
            backup_existing (bool): Whether to backup existing .env file
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Determine .env file path
            if env_file_path is None:
                # Go up from utils to project root
                project_root = Path(__file__).parent.parent
                env_file_path = project_root / '.env'
            else:
                env_file_path = Path(env_file_path)
            
            # Read existing .env content if file exists
            existing_lines = []
            jwt_secret_line_index = -1
            
            if env_file_path.exists():
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    existing_lines = f.read().splitlines()
                
                # Check if JWT_SECRET already exists and get its line index
                for i, line in enumerate(existing_lines):
                    if line.strip().startswith('JWT_SECRET='):
                        jwt_secret_line_index = i
                        break
            
            # Backup existing .env file if requested and it exists
            if backup_existing and env_file_path.exists() and jwt_secret_line_index >= 0:
                backup_path = env_file_path.with_suffix(f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                import shutil
                shutil.copy2(env_file_path, backup_path)
                print(f"📋 Backed up existing .env to: {backup_path}")
            
            # Handle JWT_SECRET update or addition
            if jwt_secret_line_index >= 0:
                # Update existing JWT_SECRET line
                existing_lines[jwt_secret_line_index] = f'JWT_SECRET={secret}'
                action = 'updated'
            else:
                # Add JWT_SECRET at the end
                # Add a comment line before JWT_SECRET if file has content
                if existing_lines:
                    # Check if last line is empty, if not add empty line for spacing
                    if existing_lines[-1].strip():
                        existing_lines.append('')
                    existing_lines.append('# JWT Secret for authentication')
                else:
                    existing_lines.append('# JWT Secret for authentication')
                
                existing_lines.append(f'JWT_SECRET={secret}')
                action = 'added'
            
            # Write the updated content back to file
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(existing_lines))
                # Ensure file ends with newline
                if existing_lines and not existing_lines[-1] == '':
                    f.write('\n')
            
            return {
                'success': True,
                'message': f'JWT_SECRET {action} in {env_file_path}',
                'env_file_path': str(env_file_path),
                'action': action
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to save JWT_SECRET: {str(e)}',
                'error': str(e)
            }
    
    @staticmethod
    def validate_secret_strength(secret):
        """
        Validate the strength of a JWT secret
        
        Args:
            secret (str): The JWT secret to validate
            
        Returns:
            dict: Validation result with score and recommendations
        """
        score = 0
        recommendations = []
        
        # Check length
        if len(secret) >= 64:
            score += 30
        elif len(secret) >= 32:
            score += 20
        elif len(secret) >= 16:
            score += 10
        else:
            recommendations.append("Secret should be at least 32 characters long")
        
        # Check character variety
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in secret)
        has_base64 = all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in secret)
        
        variety_score = sum([has_upper, has_lower, has_digit, has_special]) * 10
        score += variety_score
        
        if not has_upper and not has_base64:
            recommendations.append("Consider including uppercase letters")
        if not has_lower and not has_base64:
            recommendations.append("Consider including lowercase letters")
        if not has_digit:
            recommendations.append("Consider including numbers")
        if not has_special and not has_base64:
            recommendations.append("Consider including special characters")
        
        # Check for common patterns
        if secret.lower() in ['secret', 'password', 'key', 'token']:
            score -= 20
            recommendations.append("Avoid common words")
        
        # Check entropy (simplified)
        unique_chars = len(set(secret))
        if unique_chars >= len(secret) * 0.7:
            score += 20
        elif unique_chars >= len(secret) * 0.5:
            score += 10
        else:
            recommendations.append("Secret has low entropy, consider more variety")
        
        # Determine strength level
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Moderate"
        elif score >= 20:
            strength = "Weak"
        else:
            strength = "Very Weak"
        
        return {
            'score': min(score, 100),
            'strength': strength,
            'is_secure': score >= 60,
            'recommendations': recommendations,
            'details': {
                'length': len(secret),
                'unique_characters': unique_chars,
                'has_uppercase': has_upper,
                'has_lowercase': has_lower,
                'has_digits': has_digit,
                'has_special': has_special,
                'appears_base64': has_base64
            }
        }

# Convenience functions
def generate_jwt_secret(length=64):
    """Generate a secure JWT secret (convenience function)"""
    return JWTSecretGenerator.generate_secure_secret(length)

def setup_jwt_secret(env_file_path=None, force_regenerate=False):
    """
    Set up JWT secret in .env file (convenience function)
    
    Args:
        env_file_path (str, optional): Path to .env file
        force_regenerate (bool): Force generation of new secret even if one exists
        
    Returns:
        dict: Setup result
    """
    try:
        # Check if JWT_SECRET already exists
        current_secret = os.getenv('JWT_SECRET')
        
        if current_secret and not force_regenerate:
            validation = JWTSecretGenerator.validate_secret_strength(current_secret)
            
            if validation['is_secure']:
                return {
                    'success': True,
                    'message': 'JWT_SECRET already exists and is secure',
                    'action': 'none',
                    'validation': validation
                }
            else:
                print("⚠️  Existing JWT_SECRET is not secure enough. Generating new one...")
        
        # Generate new secret
        secret_data = JWTSecretGenerator.generate_secret_with_metadata()
        secret = secret_data['secret']
        
        # Save to .env file
        save_result = JWTSecretGenerator.save_secret_to_env(secret, env_file_path)
        
        if save_result['success']:
            validation = JWTSecretGenerator.validate_secret_strength(secret)
            
            return {
                'success': True,
                'message': f'JWT_SECRET {save_result["action"]} successfully',
                'secret_metadata': secret_data,
                'validation': validation,
                'env_file_path': save_result['env_file_path']
            }
        else:
            return save_result
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to setup JWT_SECRET: {str(e)}',
            'error': str(e)
        }

# Example usage and testing
if __name__ == '__main__':
    print("🔐 JWT Secret Generator Utility")
    print("="*50)
    
    # Generate a secure secret
    print("\n1. Generating secure secret...")
    secret = generate_jwt_secret()
    print(f"Generated secret: {secret[:20]}...")
    
    # Validate the secret
    print("\n2. Validating secret strength...")
    validation = JWTSecretGenerator.validate_secret_strength(secret)
    print(f"Strength: {validation['strength']} (Score: {validation['score']}/100)")
    print(f"Is Secure: {validation['is_secure']}")
    
    # Generate with metadata
    print("\n3. Generating with metadata...")
    secret_with_metadata = JWTSecretGenerator.generate_secret_with_metadata()
    print(f"Algorithm: {secret_with_metadata['algorithm']}")
    print(f"Generated at: {secret_with_metadata['generated_at']}")
    
    # Generate from passphrase
    print("\n4. Generating from passphrase...")
    passphrase_secret = JWTSecretGenerator.generate_secret_from_passphrase("MySecurePassphrase2024!")
    print(f"Method: {passphrase_secret['method']}")
    print(f"Salt: {passphrase_secret['salt'][:16]}...")
    
    print("\n✅ All JWT secret operations completed!")