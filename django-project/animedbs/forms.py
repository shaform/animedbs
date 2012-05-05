from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=256)

class ProfileForm(forms.Form):
    nickname = forms.CharField(max_length=30)
    gender = forms.ChoiceField(choices = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ))
