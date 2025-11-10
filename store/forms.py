from django import forms
from .models import ContactMessage, Review, UserProfile
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


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'w-16 text-center rounded bg-gray-800 text-white'
            }),
            'text': forms.Textarea(attrs={
                'class': 'w-full rounded-xl bg-gray-800 text-white p-3',
                'rows': 3,
                'placeholder': 'Ваш отзыв...'
            }),
        }



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'city', 'gender', 'avatar']  # <--- добавлено avatar
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-800 text-white', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-800 text-white', 'placeholder': 'Фамилия'}),
            'city': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-800 text-white', 'placeholder': 'Город'}),
            'gender': forms.Select(attrs={'class': 'w-full p-2 border rounded bg-gray-800 text-white'}),
        }
