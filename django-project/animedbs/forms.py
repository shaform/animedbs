# -*- coding: utf8 -*-
import datetime
from django import forms
from django.db import connection, transaction
from django.forms.widgets import Textarea
from django.core.validators import URLValidator
from django.core.validators import MaxLengthValidator
from django.forms import ValidationError
from django.shortcuts import redirect
from django.forms.util import ErrorList
from django.http import Http404
from animedbs.xmodels import AnimeXModel


GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        )
class ObjectEntity(object):
    def __init__(self):
        self.mId = None
        self.initial = None
        self.entity_title = None
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

    def title(self):
        if self.entity_title:
            return self.entity_title
        else:
            return self.Title


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
    Title = 'Seiyu'

    def setId(self, Id):
        cursor = connection.cursor()
        cursor.execute('SELECT `Name`, `Gender`,'
                + ' `Birthday`, `Description`'
                + ' FROM `SEIYU`'
                + ' WHERE `Id` = %s;', [Id])
        row = cursor.fetchone()
        if row is None:
            raise Http404()
        self.initial = {
                'name' : row[0],
                'gender' : row[1],
                'birthday' : row[2],
                'desc' : row[3],
                }
        if self.initial['gender'] is None:
            self.initial['gender'] = 'other'
        self.entity_title = row[0]

        super(SeiyuEntity, self).setId(Id)

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
    Title = 'Songs'

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
        if row is None:
            raise Http404()
        self.initial = {
                'title' : row[0],
                'featured' : (row[1],row[2]),
                'singed_by' : row[3],
                'feature_type' : row[4],
                'lyrics' : row[5],
                }
        self.entity_title = row[0]
        super(SongEntity, self).setId(Id)
        self.setChoices()

    def nav_name(self):
        return 'nav_songs'
        
    def redirect(self):
        if self.mId:
            return redirect('animedbs.views.edit_song', self.mId)
        else:
            return redirect('animedbs.views.songs')

    def update(self):
        title = self.mForm.cleaned_data['title']
        anime, season = eval(self.mForm.cleaned_data['featured'])
        singed_by = self.mForm.cleaned_data['singed_by']
        feature_type = self.mForm.cleaned_data['feature_type']
        lyrics = self.mForm.cleaned_data['lyrics']
        if lyrics == '':
            lyrics = None
        cursor = connection.cursor()
        if self.mId:
            cursor.execute(
                    '''UPDATE `SONG` SET `Title` = %s,
                       `Featured_in_aid` = %s, `Featured_in_snum` = %s,
                       `Singed_by` = %s, `Type` = %s, `Lyrics` = %s
                       WHERE `Id` = %s;
                    ''',
                    [title, anime, season, singed_by, feature_type, lyrics, self.mId])
        else:
            cursor.execute(
                    '''INSERT INTO `SONG` (`Title`, `Featured_in_aid`,
                       `Featured_in_snum`, `Singed_by`, `Type`, `Lyrics`)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    ''',
                    [title, anime, season, singed_by, feature_type, lyrics])
        transaction.commit_unless_managed()

    def delete(self):
        if self.mId:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM `SONG` WHERE `Id` = %s;', [self.mId])
            transaction.commit_unless_managed()
            self.mId = None

class CommentForm(forms.Form):
    rating = forms.ChoiceField(choices=(
        (1,1),
        (2,2),
        (3,3),
        (4,4),
        (5,5),
        ))
    text = forms.CharField(max_length=1000, widget=Textarea)

class CommentEntity(ObjectEntity):

    Form = CommentForm
    Title = 'Comment'

    def setId(self, Ids):
        cursor = connection.cursor()
        self.mSnum = Ids[1]
        self.mCommenter = Ids[2]
        cursor.execute('''SELECT
                          `Rating`,
                          `Text`
                          FROM `COMMENTS_ON`
                          WHERE `Commentee_anime` = %s
                          AND `Commentee_season` = %s
                          AND `Commenter` = %s;
                          ''', [Ids[0], Ids[1], Ids[2]])
        row = cursor.fetchone()
        if row:
            self.initial = {
                    'rating' : row[0],
                    'text' : row[1],
                    }

        super(CommentEntity, self).setId(Ids[0])

    def nav_name(self):
        return 'nav_none'
        
    def redirect(self):
        return redirect('animedbs.views.season', self.mId, self.mSnum)

    def update(self):
        rating = self.mForm.cleaned_data['rating']
        text = self.mForm.cleaned_data['text']
        cursor = connection.cursor()

        sql = '''
        DELETE FROM `COMMENTS_ON`
        WHERE `Commenter` = %s AND `Commentee_anime` = %s
        AND `Commentee_season` = %s;
        '''
        cursor.execute(sql, [self.mCommenter, self.mId, self.mSnum])

        sql = '''
        INSERT INTO `COMMENTS_ON` (
        `Commenter`,
        `Commentee_anime`,
        `Commentee_season`,
        `Rating`,
        `Text`,
        `Datetime`)
        VALUES (%s, %s, %s, %s, %s, %s);
        '''
        cursor.execute(sql,
                [self.mCommenter, self.mId, self.mSnum,
                    rating, text, datetime.datetime.now()])
        transaction.commit_unless_managed()

    def delete(self):
        if self.mId:
            cursor = connection.cursor()
            sql = '''
            DELETE FROM `COMMENTS_ON`
            WHERE `Commenter` = %s AND `Commentee_anime` = %s
            AND `Commentee_season` = %s;
            '''
            cursor.execute(sql, [self.mCommenter, self.mId, self.mSnum])
            transaction.commit_unless_managed()

class URLListField(forms.CharField):
    widget = Textarea
    umax_length = 256

    def getList(self, value):
        URLs = value.split('\n')
        URLs = set(URLs)
        url_list = []

        for url in URLs:
            url = url.strip()
            if len(url) > 0:
                url_list.append(url)

        for url in url_list:
            if len(url) > self.umax_length:
                raise ValidationError('Some URL exceed length %d.' % self.umax_length)
            URLValidator()(url)

        return url_list

    def clean(self, value):
        super(URLListField, self).clean(value)

        return self.getList(value)
    def validate(self, value):
        super(URLListField, self).validate(value)
        self.getList(value)

class ImageForm(forms.Form):
    address = URLListField()

class AnimeImageEntity(ObjectEntity):

    Form = ImageForm
    Title = 'Image'

    def setId(self, Id):
        if AnimeXModel.getOneXModel([Id]) is None:
            raise Http404()
        cursor = connection.cursor()
        cursor.execute('SELECT `Address` FROM `ANIME_IMAGE` WHERE `Anime_id` = %s;', [Id])
        rows = cursor.fetchall()
        urls = [ x[0] for x in rows ]
        if urls:
            t = '\n'.join(urls)
            self.initial = { 'address' : t }
        super(AnimeImageEntity, self).setId(Id)

    def nav_name(self):
        return 'nav_none'
        
    def redirect(self):
        return redirect('animedbs.views.anime_images', self.mId)

    def update(self):
        url_list = self.mForm.cleaned_data['address']
        cursor = connection.cursor()

        sql = '''
        DELETE FROM `ANIME_IMAGE`
        WHERE `Anime_id` = %s;
        '''
        cursor.execute(sql, [self.mId])

        sql = '''
        INSERT INTO `ANIME_IMAGE` (
        `Anime_id`,
        `Address`)
        VALUES (%s, %s);
        '''
        for url in url_list:
            cursor.execute(sql, [self.mId, url])
        transaction.commit_unless_managed()

    def delete(self):
        pass

class AnimeCharacterImageEntity(ObjectEntity):

    Form = ImageForm
    Title = 'Image'

    def setId(self, Ids):
        cursor = connection.cursor()
        sql = '''
        SELECT *
        FROM `CHARACTER`
        WHERE `Present_in` = %s AND `Name` = %s;
        '''
        cursor.execute(sql, Ids)
        row = cursor.fetchone()
        if row is None:
            raise Http404()
        sql = '''
        SELECT `Address`
        FROM `CHARACTER_IMAGE`
        WHERE `Character_anime` = %s
        AND `Character_name` = %s;
        '''
        cursor.execute(sql, Ids)
        rows = cursor.fetchall()
        urls = [ x[0] for x in rows ]
        if urls:
            t = '\n'.join(urls)
            self.initial = { 'address' : t }

        self.mCname = Ids[1]
        super(AnimeCharacterImageEntity, self).setId(Ids[0])

    def nav_name(self):
        return 'nav_none'
        
    def redirect(self):
        return redirect('animedbs.views.edit_anime_character', self.mId, self.mCname)

    def update(self):
        url_list = self.mForm.cleaned_data['address']
        cursor = connection.cursor()

        sql = '''
        DELETE FROM `CHARACTER_IMAGE`
        WHERE `Character_anime` = %s
        AND `Character_name` = %s;
        '''
        cursor.execute(sql, [self.mId, self.mCname])

        sql = '''
        INSERT INTO `CHARACTER_IMAGE` (
        `Character_anime`,
        `Character_name`,
        `Address`)
        VALUES (%s, %s, %s);
        '''
        for url in url_list:
            cursor.execute(sql, [self.mId, self.mCname, url])
        transaction.commit_unless_managed()

    def delete(self):
        pass

class CharacterForm(forms.Form):
    name = forms.CharField(max_length=30)
    gender = forms.ChoiceField(choices=(
        ('female', 'Female'),
        ('male', 'Male'),
        (u'秀吉', u'秀吉'),
        ))
    voiced_by = forms.ChoiceField()
    desc = forms.CharField(max_length=21845, widget=Textarea, required=False)

class CharacterEntity(ObjectEntity):

    Form = CharacterForm
    Title = 'Character'

    def setChoices(self):
        self.mForm.fields['voiced_by'].choices = self.seiyu_choices

    def __init__(self):
        super(CharacterEntity, self).__init__()
        cursor = connection.cursor()
        cursor.execute('SELECT `Id`, `Name` FROM `SEIYU`;')
        self.seiyu_choices = cursor.fetchall()
        self.setChoices()

    def parse(self, data):
        super(CharacterEntity, self).parse(data)
        self.setChoices()

    def setId(self, Ids):
        cursor = connection.cursor()
        self.mCname = Ids[1]
        if Ids[1]:
            sql = '''
            SELECT `Name`, `Gender`, `Voiced_by`, `Description`
            FROM `CHARACTER`
            WHERE `Present_in` = %s AND `Name` = %s;
            '''
            cursor.execute(sql, Ids)
            row = cursor.fetchone()
            if row is None:
                raise Http404()
            self.initial = {
                    'name' : row[0],
                    'gender' : row[1],
                    'voiced_by' : row[2],
                    'desc' : row[3],
                    }
        super(CharacterEntity, self).setId(Ids[0])
        self.setChoices()

    def is_valid(self):
        valid = self.mForm.is_valid()
        if valid:
            name = self.mForm.cleaned_data['name']
            cursor = connection.cursor()
            sql = '''
            SELECT * FROM `CHARACTER`
            WHERE `Present_in` = %s AND `Name` = %s;
            '''
            cursor.execute(sql, [self.mId, name])
            row = cursor.fetchone()
            if self.mCname is None or self.mCname != name:
                if row is not None:
                    errors = self.mForm._errors.setdefault('name', ErrorList())
                    errors.append(u"Duplicate character name.")
                    return False
            elif self.mCname is not None:
                if row is None:
                    errors = self.mForm._errors.setdefault('name', ErrorList())
                    errors.append(u"Character no longer exists.")
                    return False
            return True
        else:
            return False

    def nav_name(self):
        return 'nav_animes'
        
    def redirect(self):
        return redirect('animedbs.views.anime', self.mId)

    def update(self):
        cursor = connection.cursor()
        name = self.mForm.cleaned_data['name']
        gender = self.mForm.cleaned_data['gender']
        voiced_by = self.mForm.cleaned_data['voiced_by']
        desc = self.mForm.cleaned_data['desc']
        if self.mCname:
            sql = '''
            UPDATE `CHARACTER` SET `Name` = %s,
            `Gender` = %s,
            `Voiced_by` = %s,
            `Description` = %s
            WHERE `Name` = %s;
            '''
            cursor.execute(sql, [name, gender, voiced_by, desc, self.mCname])
        else:
            sql = '''
            INSERT INTO `CHARACTER` (`Present_in`, `Name`, `Gender`, `Voiced_by`, `Description`)
            VALUES (%s, %s, %s, %s, %s);
            '''
            cursor.execute(sql, [self.mId, name, gender, voiced_by, desc])

        transaction.commit_unless_managed()

    def delete(self):
        if self.mCname:
            cursor = connection.cursor()
            cursor.execute('''
            DELETE FROM `CHARACTER`
            WHERE `Present_in` = %s
            AND `Name` = %s;
            ''', [self.mId, self.mCname])
            transaction.commit_unless_managed()
            self.mCname = None

class SeasonForm(forms.Form):
    series_num = forms.IntegerField(min_value=1)
    full_name = forms.CharField(max_length=100)
    total_episodes = forms.IntegerField(min_value=1)
    release_year = forms.IntegerField(min_value=0, max_value=2020)
    release_month = forms.IntegerField(min_value=1, max_value=12)

class SeasonEntity(ObjectEntity):

    Form = SeasonForm
    Title = 'Season'

    def setId(self, Ids):
        self.mSnum = Ids[1]
        if len(Ids) == 2 and Ids[1]:
            cursor = connection.cursor()
            sql = '''
            SELECT `Full_name`, `Total_episodes`, `Release_year`, `Release_month`
            FROM `SEASON`
            WHERE `Part_of` = %s AND `Series_num` = %s;
            '''
            cursor.execute(sql, Ids)
            row = cursor.fetchone()
            if row is None:
                raise Http404()
            self.initial = {
                    'series_num' : Ids[1],
                    'full_name' : row[0],
                    'total_episodes' : row[1],
                    'release_year' : row[2],
                    'release_month' : row[3],
                    }
            self.entity_title = row[0]
        super(SeasonEntity, self).setId(Ids[0])

    def is_valid(self):
        valid = self.mForm.is_valid()
        if valid:
            series_num = self.mForm.cleaned_data['series_num']
            cursor = connection.cursor()
            sql = '''
            SELECT * FROM `SEASON`
            WHERE `Part_of` = %s AND `Series_num` = %s;
            '''
            cursor.execute(sql, [self.mId, series_num])
            row = cursor.fetchone()
            if self.mSnum is None or self.mSnum != series_num:
                if row is not None:
                    errors = self.mForm._errors.setdefault('series_num', ErrorList())
                    errors.append(u"Duplicate series number.")
                    return False
            elif self.mSnum is not None:
                if row is None:
                    errors = self.mForm._errors.setdefault('series_num', ErrorList())
                    errors.append(u"Season no longer exists.")
                    return False
            return True
        else:
            return False

    def nav_name(self):
        return 'nav_animes'
        
    def redirect(self):
        if self.mSnum:
            return redirect('animedbs.views.season', self.mId, self.mSnum)
        else:
            return redirect('animedbs.views.anime', self.mId)

    def update(self):
        series_num = self.mForm.cleaned_data['series_num']
        full_name = self.mForm.cleaned_data['full_name']
        total_episodes = self.mForm.cleaned_data['total_episodes']
        release_year = self.mForm.cleaned_data['release_year']
        release_month = self.mForm.cleaned_data['release_month']
        cursor = connection.cursor()

        if self.mSnum:
            cursor.execute(
                    '''UPDATE `SEASON` SET `Series_num` = %s, `Full_name` = %s,
                       `Total_episodes` = %s, `Release_year` = %s,
                       `Release_month` = %s
                       WHERE `Part_of` = %s AND `Series_num` = %s;
                    ''',
                    [series_num, full_name, total_episodes,
                        release_year, release_month, self.mId, self.mSnum])
            self.mSnum = series_num
        else:
            cursor.execute(
                    '''INSERT INTO `SEASON` (`Part_of`, `Series_num`, `Full_name`,
                       `Total_episodes`, `Release_year`, `Release_month`)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    ''',
                    [self.mId, series_num, full_name, total_episodes,
                        release_year, release_month])
        transaction.commit_unless_managed()

    def delete(self):
        if self.mSnum:
            cursor = connection.cursor()
            sql = '''
            DELETE FROM `SEASON`
            WHERE `Part_of` = %s AND `Series_num` = %s;
            '''
            cursor.execute(sql, [self.mId, self.mSnum])
            transaction.commit_unless_managed()
            self.mSnum = None

class AnimeForm(forms.Form):
    title = forms.CharField(max_length=100)
    authored_by = forms.ChoiceField()
    desc = forms.CharField(max_length=21845, widget=Textarea, required=False)
    address = forms.URLField(max_length=512, required=False)

class AnimeEntity(ObjectEntity):

    Form = AnimeForm
    Title = 'Create Anime'

    def setChoices(self):
        self.mForm.fields['authored_by'].choices = self.author_choices

    def __init__(self):
        super(AnimeEntity, self).__init__()
        cursor = connection.cursor()
        cursor.execute('SELECT `Id`, `Name` FROM `AUTHOR`;')
        self.author_choices = cursor.fetchall()
        self.setChoices()

    def parse(self, data):
        super(AnimeEntity, self).parse(data)
        self.setChoices()

    def setId(self, Id):
        anime = AnimeXModel.getOneXModel([Id])
        if anime is None:
            raise Http404()
        self.initial = {
                'title' : anime.Title,
                'authored_by' : anime.Authored_by,
                'desc' : anime.Description,
                'address' : anime.Web_address
                }
        self.entity_title = anime.Title
        super(AnimeEntity, self).setId(Id)
        self.setChoices()

    def nav_name(self):
        return 'nav_animes'
        
    def redirect(self):
        if self.mId:
            return redirect('animedbs.views.anime', self.mId)
        else:
            return redirect('animedbs.views.animes')

    def is_valid(self):
        valid = self.mForm.is_valid()
        if valid:
            title = self.mForm.cleaned_data['title']
            cursor = connection.cursor()
            sql = '''
            SELECT `Id` FROM `ANIME`
            WHERE `Title` = %s;
            '''
            cursor.execute(sql, [title])
            row = cursor.fetchone()
            if (self.mId is None and row is not None) or (
                    self.mId is not None and row is not None and self.mId != row[0]):
                errors = self.mForm._errors.setdefault('title', ErrorList())
                errors.append(u"Duplicate title.")
                return False
            return True
        else:
            return False
    def update(self):
        title = self.mForm.cleaned_data['title']
        authored_by = self.mForm.cleaned_data['authored_by']
        desc = self.mForm.cleaned_data['desc']
        address = self.mForm.cleaned_data['address']

        cursor = connection.cursor()
        if self.mId:
            sql = '''
            UPDATE `ANIME`
            SET `Title` = %s, `Authored_by` = %s,
            `Description` = %s, `Web_address` = %s
            WHERE `Id` = %s;
            '''
            cursor.execute(sql,
                    [title, authored_by, desc, address, self.mId])
        else:
            sql = '''
            INSERT INTO `ANIME`
            (`Title`, `Authored_by`, `Description`, `Web_address`)
            VALUES (%s, %s, %s, %s);
            '''
            cursor.execute(sql,
                    [title, authored_by, desc, address])

        transaction.commit_unless_managed()

    def delete(self):
        if self.mId:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM `ANIME` WHERE `Id` = %s;', [self.mId])
            transaction.commit_unless_managed()
            self.mId = None
