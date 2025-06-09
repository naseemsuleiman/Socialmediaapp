from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email


from django import forms
from .models import Profile, Post

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'location', 'website']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image', 'hashtags']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
            'hashtags': forms.TextInput(attrs={'placeholder': 'comma,separated,values'}),
        }