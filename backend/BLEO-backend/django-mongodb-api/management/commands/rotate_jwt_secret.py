from django.core.management.base import BaseCommand
from utils.jwt_rotation import JWTSecretRotationManager

class Command(BaseCommand):
    help = 'Rotate JWT secret key'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rotation even if not due',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show rotation status only',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check if rotation is needed',
        )
    
    def handle(self, *args, **options):
        manager = JWTSecretRotationManager()
        
        if options['status']:
            status = manager.get_rotation_status()
            self.stdout.write(f"🔄 JWT Secret Rotation Status")
            self.stdout.write(f"Status: {status['status']}")
            self.stdout.write(f"Message: {status['message']}")
            if status['status'] != 'error':
                self.stdout.write(f"Last Rotation: {status['last_rotation']}")
                self.stdout.write(f"Next Rotation: {status['next_rotation']}")
                self.stdout.write(f"Rotation Count: {status['rotation_count']}")
            return
        
        if options['check']:
            needs_rotation = manager.needs_rotation()
            if needs_rotation:
                self.stdout.write(self.style.WARNING('🔄 JWT secret rotation is needed'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ JWT secret rotation is current'))
            return
        
        # Perform rotation
        result = manager.rotate_secret(force=options['force'])
        
        if result['success']:
            if result['rotated']:
                self.stdout.write(self.style.SUCCESS(f"✅ {result['message']}"))
                self.stdout.write(f"🔢 Rotation count: {result['rotation_count']}")
                self.stdout.write(f"📅 Next rotation: {result['next_rotation']}")
                self.stdout.write(f"🔒 Secret strength: {result['secret_strength']['strength']}")
            else:
                self.stdout.write(self.style.SUCCESS(f"ℹ️  {result['message']}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {result['message']}"))