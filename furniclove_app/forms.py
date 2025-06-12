from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import admin
from .models import UserProfile
from .models import Review



class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        strip=False  # This prevents Django from trimming spaces automatically
    )
    email = forms.EmailField(
        max_length=100, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')

        print(f"DEBUG: Checking username validation - '{username}'")  # Debugging line

        if username.startswith(" "):
            raise ValidationError("Username should not start with a space")

        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Passwords do not match")

        # Check if email is already in use
        if User.objects.filter(email=cleaned_data.get('email')).exists():
            raise ValidationError("The email ID is already used")

        return cleaned_data


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone']  # Include username and email

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        user = self.user

        # Update the User model fields
        user.username = self.cleaned_data.get('username', user.username)
        user.email = self.cleaned_data.get('email', user.email)

        if commit:
            user.save()
            user_profile.save()

        return user_profile


class ReturnReasonForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter reason for return'}), label="Reason for Return")



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']