from django import forms
from django.contrib.auth.models import User


class UpdateProfileForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']