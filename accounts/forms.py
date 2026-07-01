from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegisterForm(UserCreationForm):
    PUBLIC_ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('worker', 'Worker'),
    ]

    full_name = forms.CharField(max_length=120, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=30, required=False)
    role = forms.ChoiceField(choices=PUBLIC_ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email', 'phone_number', 'role', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name']
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        if commit:
            user.save()
            role = self.cleaned_data['role']
            import secrets
            UserProfile.objects.create(
                user=user,
                full_name=full_name,
                role=role,
                phone_number=self.cleaned_data.get('phone_number', ''),
                is_customer=role == 'customer',
                is_worker=role == 'worker',
                phone_verification_code=secrets.randbelow(900000) + 100000,
            )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('full_name', 'phone_number')
