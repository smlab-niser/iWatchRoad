from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend to allow users to log in using either their username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # If no username is passed, check kwargs (sometimes used by DRF/SimpleJWT)
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
            
        if not username:
            return None

        try:
            # Check if user exists by either username or email (case-insensitive)
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # If multiple users have the same email (shouldn't happen with our validation, but just in case)
            user = UserModel.objects.filter(email__iexact=username).order_by('id').first()

        # Check the password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        return None
