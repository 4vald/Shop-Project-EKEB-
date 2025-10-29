from django import forms
from .models import ContactMessage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 rounded bg-secondary text-gray-200', 'placeholder': 'Ваше имя'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 rounded bg-secondary text-gray-200', 'placeholder': 'Ваш email'}),
            'subject': forms.TextInput(attrs={'class': 'w-full p-3 rounded bg-secondary text-gray-200', 'placeholder': 'Тема'}),
            'message': forms.Textarea(attrs={'class': 'w-full p-3 rounded bg-secondary text-gray-200', 'placeholder': 'Сообщение'}),
        }



class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
