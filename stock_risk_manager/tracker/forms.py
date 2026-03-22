from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UpdateProfileForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


# Registration form with validation

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")

        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)  # Django validation
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError("Passwords do not match")

