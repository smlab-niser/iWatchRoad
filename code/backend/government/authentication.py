from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .models import GovUser
import hashlib


class GovTokenAuthentication(BaseAuthentication):
    """
    Custom token authentication for government users
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            prefix, token = auth_header.split(' ', 1)
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None
            
        # For now, we'll use a simple approach - store tokens in cache or session
        # In production, you'd want a proper token storage mechanism
        
        # Since we're generating deterministic tokens, we can validate them
        # by checking if any user's token matches
        try:
            # Try to find a user that could have generated this token
            # This is a simplified approach for development
            users = GovUser.objects.using('government').all()
            
            for user in users:
                # Generate expected token for this user
                import secrets
                # This won't work as expected because secrets.token_urlsafe() generates random tokens
                # We need a different approach
                pass
                
        except Exception:
            return None
            
        return None
        
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer'
