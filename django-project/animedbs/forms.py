import datetime
from django import forms
from django.db import connection, transaction
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

class SeiyuEntity(object):

    def __init__(self):
        self.mForm = SeiyuForm()
        self.mId = None

    def form(self):
        return self.mForm

    def parse(self, data):
        self.mForm = SeiyuForm(data)

    def setId(Id):
        self.mId = Id

    def is_valid(self):
        return self.mForm.is_valid()

    def title(self):
        return 'Seiyu'

    def redirect(self):
        return 'animedbs.views.seiyus'

    def update(self):
        cursor = connection.cursor()
        name = self.mForm.cleaned_data['name']
        gender = self.mForm.cleaned_data['gender']
        if gender == 'other':
            gender = None
        birthday = self.mForm.cleaned_data['birthday']
        desc = self.mForm.cleaned_data['desc']
        if desc == '':
            desc = None
        if self.mId:
            cursor.execute('UPDATE `SEIYU` SET `Name` = %s,'
                    + '`Gender` = %s, `Birthday` = %s, `Description` = %s'
                    + 'WHERE `Id` = %s;',
                    [name, gender, birthday, desc, self.mId])
        else:
            cursor.execute('INSERT INTO `SEIYU` (`Name`, `Gender`,'
                    + '`Birthday`, `Description`)'
                    + 'VALUES (%s, %s, %s, %s);',
                    [name, gender, birthday, desc])

        transaction.commit_unless_managed()

class SeiyuEntity(object):

    def __init__(self):
        self.mForm = SeiyuForm()
        self.mId = None

    def form(self):
        return self.mForm

    def parse(self, data):
        self.mForm = SeiyuForm(data)

    def setId(Id):
        self.mId = Id

    def is_valid(self):
        return self.mForm.is_valid()

    def title(self):
        return 'Seiyu'

    def redirect(self):
        return 'animedbs.views.seiyus'

    def update(self):
        cursor = connection.cursor()
        name = self.mForm.cleaned_data['name']
        gender = self.mForm.cleaned_data['gender']
        if gender == 'other':
            gender = None
        birthday = self.mForm.cleaned_data['birthday']
        desc = self.mForm.cleaned_data['desc']
        if desc == '':
            desc = None
        if self.mId:
            cursor.execute('UPDATE `SEIYU` SET `Name` = %s,'
                    + '`Gender` = %s, `Birthday` = %s, `Description` = %s'
                    + 'WHERE `Id` = %s;',
                    [name, gender, birthday, desc, self.mId])
        else:
            cursor.execute('INSERT INTO `SEIYU` (`Name`, `Gender`,'
                    + '`Birthday`, `Description`)'
                    + 'VALUES (%s, %s, %s, %s);',
                    [name, gender, birthday, desc])

        transaction.commit_unless_managed()
