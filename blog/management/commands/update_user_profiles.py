from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blog.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create or update user profiles for all users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        updated_count = 0

        for user in users:
            try:
                # Try to get the user's profile
                profile = user.profile
                updated_count += 1
            except UserProfile.DoesNotExist:
                # Create a profile if it doesn't exist
                UserProfile.objects.create(user=user)
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed user profiles:\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}'
            )
        ) 