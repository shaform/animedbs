import datetime
from django import forms
from django.forms.widgets import Textarea

GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        )

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=256)

class ProfileForm(forms.Form):
    nickname = forms.CharField(max_length=30)
    gender = forms.ChoiceField(choices = GENDERS)

class SearchForm(forms.Form):
    keyword = forms.CharField(max_length=30)

class SeiyuForm(forms.Form):
    name = forms.CharField(max_length=30)
    gender = forms.ChoiceField(choices = GENDERS)
    birthday = forms.DateField(initial=datetime.date.today, required=False)
    desc = forms.CharField(max_length=21845, widget=Textarea, required=False)
