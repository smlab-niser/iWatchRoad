from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    UserSerializer,
    get_legacy_role,
)
import re


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with email validation."""
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['email'].help_text = 'Required. Enter a valid email address.'
        
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        
        # Basic email validation
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError("Enter a valid email address.")
        
        return email


def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Make the user staff so they can access admin
            user.is_staff = True
            user.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login to admin.')
            
            # Auto login the user
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('/admin/')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def check_admin_status(request):
    """API endpoint to check if user has admin access."""
    if request.user.is_authenticated and request.user.is_staff:
        return JsonResponse({
            'has_admin_access': True,
            'username': request.user.username,
            'email': request.user.email
        })
    return JsonResponse({'has_admin_access': False})


@login_required
def admin_dashboard(request):
    """Custom admin dashboard view."""
    return render(request, 'admin/dashboard.html', {
        'user': request.user,
        'title': 'iWatchRoad Admin'
    })


# ---------------------------------------------------------------------------
# Mobile (JWT) API views
#
# Ported from iwatchroad/backend as an ADDITIVE change -- see
# Plan/BACKEND_PROGRESS.md. These views build the {success, message, data}
# envelope themselves, so they do NOT require a custom DRF renderer. The
# project-wide JSONRenderer stays as-is and the React SPA is unaffected.
# ---------------------------------------------------------------------------


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login returning tokens, the user object, and a legacy role."""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


class CitizenRegistrationView(APIView):
    """Register a citizen user without staff elevation."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Citizen account created successfully.',
                'data': {
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Return the authenticated user's profile and role."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'data': {
                'user': serializer.data,
                'role': get_legacy_role(request.user)
            }
        }, status=status.HTTP_200_OK)


class FirebaseLoginView(APIView):
    """
    Exchange a Firebase ID token for a Django JWT (Google sign-in).

    firebase_admin is imported lazily and the app is initialised on first use:
    serviceAccountKey.json is not present in this deployment, so an eager
    import would break every other view in this module. Without the key this
    endpoint returns 503 and the rest of the auth API keeps working.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = (
            request.data.get('id_token')
            or request.data.get('idToken')
            or request.data.get('token')
        )
        if not id_token:
            return Response(
                {'success': False, 'message': 'No token provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import firebase_admin
            from firebase_admin import auth as firebase_auth, credentials
        except ImportError:
            return Response(
                {'success': False,
                 'message': 'Google sign-in is not configured on this server.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not firebase_admin._apps:
            from django.conf import settings as django_settings
            import os
            cred_path = os.path.join(django_settings.BASE_DIR, 'serviceAccountKey.json')
            if not os.path.exists(cred_path):
                return Response(
                    {'success': False,
                     'message': 'Google sign-in is not configured on this server.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            firebase_admin.initialize_app(credentials.Certificate(cred_path))

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            email = decoded_token.get('email')
            name = decoded_token.get('name', '')

            if not email:
                return Response(
                    {'success': False, 'message': 'No email found in token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': name},
            )
            if created:
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data,
                    'role': get_legacy_role(user),
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
