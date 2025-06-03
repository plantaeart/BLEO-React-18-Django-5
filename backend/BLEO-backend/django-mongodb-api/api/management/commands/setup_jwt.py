"""CLI script to set up JWT secret"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.jwt_utils import setup_jwt_secret, JWTSecretGenerator

def main():
    print("🔐 BLEO JWT Secret Setup")
    print("="*40)
    
    choice = input("\nChoose setup method:\n1. Auto-generate secure secret\n2. Generate from passphrase\n3. Validate existing secret\n\nEnter choice (1-3): ")
    
    if choice == '1':
        result = setup_jwt_secret(force_regenerate=True)
        if result['success']:
            print(f"\n✅ {result['message']}")
            print(f"🔒 Strength: {result['validation']['strength']} ({result['validation']['score']}/100)")
        else:
            print(f"\n❌ {result['message']}")
    
    elif choice == '2':
        passphrase = input("\nEnter passphrase: ")
        secret_data = JWTSecretGenerator.generate_secret_from_passphrase(passphrase)
        
        save_result = JWTSecretGenerator.save_secret_to_env(secret_data['secret'])
        if save_result['success']:
            print(f"\n✅ JWT_SECRET generated from passphrase and saved!")
            validation = JWTSecretGenerator.validate_secret_strength(secret_data['secret'])
            print(f"🔒 Strength: {validation['strength']} ({validation['score']}/100)")
        else:
            print(f"\n❌ {save_result['message']}")
    
    elif choice == '3':
        current_secret = os.getenv('JWT_SECRET')
        if not current_secret:
            print("\n❌ No JWT_SECRET found in environment")
            return
            
        validation = JWTSecretGenerator.validate_secret_strength(current_secret)
        print(f"\n📊 Current JWT_SECRET validation:")
        print(f"🔒 Strength: {validation['strength']} ({validation['score']}/100)")
        print(f"✅ Secure: {validation['is_secure']}")
        
        if validation['recommendations']:
            print("\n💡 Recommendations:")
            for rec in validation['recommendations']:
                print(f"  • {rec}")
    
    else:
        print("\n❌ Invalid choice")

if __name__ == '__main__':
    main()