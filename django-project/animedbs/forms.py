import datetime
from django import forms
from django.db import connection, transaction
from django.forms.widgets import Textarea
from django.shortcuts import redirect

GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        )
class ObjectEntity(object):
    def __init__(self):
        self.mId = None
        self.initial = None
        self.mForm = self.Form()

    def form(self):
        return self.mForm

    def parse(self, data):
        self.mForm = self.Form(data, initial=self.initial)

    def is_valid(self):
        return self.mForm.is_valid()

    def setId(self, Id):
        self.mId = Id
        self.mForm = self.Form(initial=self.initial)


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

class SeiyuEntity(ObjectEntity):

    Form = SeiyuForm

    def setId(self, Id):
        cursor = connection.cursor()
        cursor.execute('SELECT `Name`, `Gender`,'
                + ' `Birthday`, `Description`'
                + ' FROM `SEIYU`'
                + ' WHERE `Id` = %s;', [Id])
        row = cursor.fetchone()
        self.initial = {
                'name' : row[0],
                'gender' : row[1],
                'birthday' : row[2],
                'desc' : row[3],
                }
        if self.initial['gender'] is None:
            self.initial['gender'] = 'other'

        super(SeiyuEntity, self).setId(Id)

    def title(self):
        return 'Seiyu'

    def nav_name(self):
        return 'nav_seiyus'
        
    def redirect(self):
        if self.mId:
            return redirect('animedbs.views.seiyu', self.mId)
        else:
            return redirect('animedbs.views.seiyus')

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
                    + ' `Gender` = %s, `Birthday` = %s, `Description` = %s'
                    + ' WHERE `Id` = %s;',
                    [name, gender, birthday, desc, self.mId])
        else:
            cursor.execute('INSERT INTO `SEIYU` (`Name`, `Gender`,'
                    + ' `Birthday`, `Description`)'
                    + ' VALUES (%s, %s, %s, %s);',
                    [name, gender, birthday, desc])

        transaction.commit_unless_managed()


class SongForm(forms.Form):
    title = forms.CharField(max_length=100)
    featured = forms.ChoiceField()
    singed_by = forms.ChoiceField()
    feature_type = forms.ChoiceField(choices=(
        ('op', 'Opening'),
        ('ed', 'Ending'),
        ))
    lyrics = forms.CharField(max_length=21845, widget=Textarea, required=False)

class SongEntity(ObjectEntity):

    Form = SongForm

    def setChoices(self):
        self.mForm.fields['featured'].choices = self.feature_choices
        self.mForm.fields['singed_by'].choices = self.seiyu_choices

    def __init__(self):
        super(SongEntity, self).__init__()
        cursor = connection.cursor()
        cursor.execute('SELECT `Id`, `Name` FROM `SEIYU`;')
        self.seiyu_choices = cursor.fetchall()
        cursor.execute('SELECT `Part_of`, `Series_num`, `Full_name` FROM `SEASON`;')
        rows = cursor.fetchall()
        self.feature_choices = [((x[0], x[1]), '%d - %s' % (x[1], x[2])) for x in rows]
        self.setChoices()

    def parse(self, data):
        super(SongEntity, self).parse(data)
        self.setChoices()

    def setId(self, Id):
        cursor = connection.cursor()
        cursor.execute('''SELECT
                          `Title`,
                          `Featured_in_aid`,
                          `Featured_in_snum`,
                          `Singed_by`,
                          `Type`,
                          `Lyrics`
                          FROM `SONG`
                          WHERE `Id` = %s;''', [Id])
        row = cursor.fetchone()
        self.initial = {
                'title' : row[0],
                'featured' : (row[1],row[2]),
                'singed_by' : row[3],
                'feature_type' : row[4],
                'lyrics' : row[5],
                }
        super(SongEntity, self).setId(Id)
        self.setChoices()

    def title(self):
        return 'Song'

    def nav_name(self):
        return 'nav_songs'
        
    def redirect(self):
        if self.mId:
            return redirect('animedbs.views.seiyus')
        else:
            return redirect('animedbs.views.seiyus')

    def update(self):
        pass
