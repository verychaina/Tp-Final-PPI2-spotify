from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')

    class Meta:
        model = User
        fields = ['username', 'email', 'telefono', 'password1', 'password2']
