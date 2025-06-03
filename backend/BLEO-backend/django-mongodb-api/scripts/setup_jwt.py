#!/usr/bin/env python
"""CLI script to set up JWT secret"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env if it exists
from dotenv import load_dotenv
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)

from utils.jwt_utils import setup_jwt_secret, JWTSecretGenerator

def main():
    print("🔐 BLEO JWT Secret Setup")
    print("="*40)
    
    # Show current .env file status
    if env_file.exists():
        print(f"📁 Found .env file: {env_file}")
        current_secret = os.getenv('JWT_SECRET')
        if current_secret:
            print("🔑 JWT_SECRET already exists in environment")
            
            # Show rotation status
            from utils.jwt_rotation import get_jwt_rotation_status
            status = get_jwt_rotation_status()
            print(f"🔄 Rotation Status: {status['message']}")
        else:
            print("❌ JWT_SECRET not found in .env file")
    else:
        print(f"📁 .env file will be created: {env_file}")
    
    choice = input("\nChoose setup method:\n1. Auto-generate secure secret\n2. Generate from passphrase\n3. Validate existing secret\n4. Show current .env content\n5. Check rotation status\n6. Rotate secret now\n\nEnter choice (1-6): ")
    
    if choice == '1':
        result = setup_jwt_secret(force_regenerate=True)
        if result['success']:
            print(f"\n✅ {result['message']}")
            print(f"🔒 Strength: {result['validation']['strength']} ({result['validation']['score']}/100)")
            print(f"📁 File: {result['env_file_path']}")
        else:
            print(f"\n❌ {result['message']}")
    
    elif choice == '2':
        passphrase = input("\nEnter passphrase: ")
        if not passphrase.strip():
            print("❌ Passphrase cannot be empty")
            return
            
        secret_data = JWTSecretGenerator.generate_secret_from_passphrase(passphrase)
        
        save_result = JWTSecretGenerator.save_secret_to_env(secret_data['secret'])
        if save_result['success']:
            print(f"\n✅ JWT_SECRET generated from passphrase and {save_result['action']}!")
            validation = JWTSecretGenerator.validate_secret_strength(secret_data['secret'])
            print(f"🔒 Strength: {validation['strength']} ({validation['score']}/100)")
            print(f"📁 File: {save_result['env_file_path']}")
        else:
            print(f"\n❌ {save_result['message']}")
    
    elif choice == '3':
        # Reload environment to get any newly added JWT_SECRET
        if env_file.exists():
            load_dotenv(env_file, override=True)
        
        current_secret = os.getenv('JWT_SECRET')
        if not current_secret:
            print("\n❌ No JWT_SECRET found in environment")
            print("💡 Use option 1 or 2 to generate one")
            return
            
        validation = JWTSecretGenerator.validate_secret_strength(current_secret)
        print(f"\n📊 Current JWT_SECRET validation:")
        print(f"🔒 Strength: {validation['strength']} ({validation['score']}/100)")
        print(f"✅ Secure: {validation['is_secure']}")
        print(f"📏 Length: {validation['details']['length']} characters")
        
        if validation['recommendations']:
            print("\n💡 Recommendations:")
            for rec in validation['recommendations']:
                print(f"  • {rec}")
        
        if validation['is_secure']:
            print("\n🎉 Your JWT_SECRET is secure and ready to use!")
        else:
            print("\n⚠️  Consider generating a new JWT_SECRET using option 1")
    
    elif choice == '4':
        if env_file.exists():
            print(f"\n📄 Current .env file content ({env_file}):")
            print("-" * 50)
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    # Hide sensitive values for security
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip():
                            # Check for sensitive environment variables
                            line_upper = line.upper()
                            if (line.strip().startswith('JWT_SECRET=') or
                                'PASSWORD' in line_upper or
                                'SECRET' in line_upper or
                                'KEY=' in line_upper or
                                'TOKEN=' in line_upper or
                                'API_KEY' in line_upper or
                                'PRIVATE_KEY' in line_upper or
                                'SALT=' in line_upper):
                                
                                # Extract the variable name (before =)
                                if '=' in line:
                                    var_name = line.split('=')[0]
                                    print(f'{var_name}=***[HIDDEN]***')
                                else:
                                    print(line)  # Print as-is if no = found
                            else:
                                print(line)
                        else:
                            print(line)  # Print empty lines as-is
                else:
                    print("(file is empty)")
            print("-" * 50)
        else:
            print(f"\n📄 .env file does not exist yet: {env_file}")
    
    elif choice == '5':
        from utils.jwt_rotation import get_jwt_rotation_status
        status = get_jwt_rotation_status()
        
        print(f"\n🔄 JWT Secret Rotation Status:")
        print(f"Status: {status['status']}")
        print(f"Message: {status['message']}")
        
        if status['status'] != 'error':
            print(f"Last Rotation: {status['last_rotation']}")
            print(f"Next Rotation: {status['next_rotation']}")
            print(f"Days Since Last: {status['days_since_last']}")
            print(f"Days Until Next: {status['days_until_next']}")
            print(f"Total Rotations: {status['rotation_count']}")
            print(f"Rotation Interval: {status['rotation_days']} days")
    
    elif choice == '6':
        from utils.jwt_rotation import rotate_jwt_secret
        
        force = input("\nForce rotation even if not due? (y/N): ").lower() == 'y'
        result = rotate_jwt_secret(force=force)
        
        if result['success']:
            if result['rotated']:
                print(f"\n✅ {result['message']}")
                print(f"🔢 Rotation count: {result['rotation_count']}")
                print(f"📅 Next rotation: {result['next_rotation']}")
            else:
                print(f"\nℹ️  {result['message']}")
        else:
            print(f"\n❌ {result['message']}")
    else:
        print("\n❌ Invalid choice")

if __name__ == '__main__':
    main()