from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
