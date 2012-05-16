import datetime
import decimal
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.template import Context
from animedbs.forms import LoginForm
from animedbs.forms import ProfileForm
from animedbs.forms import SeiyuEntity
from animedbs.forms import SongEntity
from animedbs.forms import CommentEntity
from animedbs.forms import AnimeImageEntity
from animedbs.forms import AnimeEntity
from animedbs.forms import AnimeCharacterImageEntity
from animedbs.forms import CharacterEntity
from animedbs.forms import SeasonEntity
from animedbs.forms import AuthorEntity
from django import forms
from django.template import Template

def login_required(function):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('animedbs.views.home')
            else:
                return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)




#### -- Home Page -- ####
def index(request):
    return render_to_response('index.html',
            context_instance=RequestContext(request))

def logout(request):
    for key in request.session.keys():
        del request.session[key]
    return redirect('animedbs.views.home')

def register(request, email):
    cursor = connection.cursor()

    cursor.execute('INSERT INTO `USER` (Email, Nickname, Gender)'
            + 'VALUES (%s, %s, %s);', [email, 'Guest', 'other'])
    transaction.commit_unless_managed()

    cursor.execute('SELECT `Id`, `Nickname` FROM `USER` WHERE Email = %s', [email])
    row = cursor.fetchone()
    request.session['user_id'] = row[0]
    request.session['user_name'] = row[1]

    return redirect('animedbs.views.profile')

def login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cursor = connection.cursor()

            # check if account exists
            email = form.cleaned_data['email']
            cursor.execute('SELECT `Id`, `Nickname` FROM `USER` WHERE Email = %s', [email])
            row = cursor.fetchone()

            if row is None:
                return register(request, email)
            else:
                request.session['user_id'] = row[0]
                request.session['user_name'] = row[1]
                return redirect('animedbs.views.home')

    return render_to_response('login.html', {
        'form' : form,
        }, context_instance=RequestContext(request))

def home(request):
    if 'user_id' not in request.session:
        return login(request)
    else:
        return index(request)



## -- Users -- ##

@login_required
def profile(request):
    if 'user_id' not in request.session:
        return redirect('animedbs.views.home')

    cursor = connection.cursor()

    user_id = request.session['user_id']
    cursor.execute('SELECT `Email`, `Nickname`, `Gender`'
            + ' FROM `USER` WHERE `Id` = %s', [user_id])
    row = cursor.fetchone()
    email = row[0]
    nickname = row[1]

    form = ProfileForm(initial={
        'nickname' : row[1],
        'gender' : row[2],
        })
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data['nickname']
            gender = form.cleaned_data['gender']
            cursor.execute('UPDATE `USER` SET `Nickname` = %s, `Gender` = %s'
                    + ' WHERE `Id` = %s;', [nickname, gender, user_id])
            transaction.commit_unless_managed()
            request.session['user_name'] = nickname
            return redirect('animedbs.views.profile')

    cursor.execute('SELECT `Commentee_anime`, `Commentee_season`,'
            + ' `Rating`, `Text`, `Datetime`'
            + ' FROM `COMMENTS_ON` WHERE `Commenter` = %s;', [user_id])
    rows = cursor.fetchall()
    comments = []

    for cmt in rows:
        cursor.execute('SELECT `Title`'
                + ' FROM `ANIME` WHERE `Id` = %s;', [cmt[0]])
        anime = cursor.fetchone()[0]
        cursor.execute('SELECT `Full_name`'
                + ' FROM `SEASON` WHERE `Part_of` = %s'
                + ' AND `Series_num` = %s;', [cmt[0], cmt[1]])
        season = cursor.fetchone()[0]
        comments.append({
            'anime' : anime,
            'season' : season,
            'anime_id' : cmt[0],
            'commenter_id' : user_id,
            'snum' : cmt[1],
            'rating' : cmt[2],
            'text' : cmt[3],
            'datetime' : cmt[4],
            })

    return render_to_response('profile.html', {
        'email' : email,
        'form' : form,
        'username' : nickname,
        'comments' : comments,
        }, context_instance=RequestContext(request))


@login_required
def comment(request, aid, snum):
    cursor = connection.cursor()

    user_id = request.session['user_id']

    sql = '''
    SELECT * FROM `COMMENTS_ON`
    WHERE `Commenter` = %s AND `Commentee_anime` = %s
    AND `Commentee_season` = %s;
    '''
    cursor.execute(sql, [user_id, aid, snum])

    if cursor.fetchone() is None:
        return create_entity(request, CommentEntity, [int(aid), int(snum), int(user_id)])
    else:
        return create_entity(request, CommentEntity, [int(aid), int(snum), int(user_id)], True)


@login_required
def users(request):
    cursor = connection.cursor()
    sql = '''
    SELECT `Id`, `Email`, `Nickname`, `Gender`
    FROM `USER`;
    '''
    cursor.execute(sql)
    
    rows = cursor.fetchall()
    
    cols = [
        ('number','Id'),
        ('string','Email'),
        ('string','Nickname'),
        ('string','Gender'),
    ]

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.user', args=[row[0]]))

    return render_to_response('table.html', {
        'nav_users' : True,
        'pagetitle' : 'Users',
        'cols' : cols,
        'rows' : json.dumps(rows),
        'rowlinks' : json.dumps(rowlinks),
        }, context_instance=RequestContext(request))

@login_required
def user(request, user_id):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Email`, `Nickname`, `Gender`'
            + ' FROM `USER` WHERE `Id` = %s;', [user_id])
    row = cursor.fetchone()

    if row is None:
        raise Http404

    cursor.execute('SELECT `Commentee_anime`, `Commentee_season`,'
            + ' `Rating`, `Text`, `Datetime`'
            + ' FROM `COMMENTS_ON` WHERE `Commenter` = %s;', [user_id])
    rows = cursor.fetchall()
    comments = []

    for cmt in rows:
        cursor.execute('SELECT `Title`'
                + ' FROM `ANIME` WHERE `Id` = %s;', [cmt[0]])
        anime = cursor.fetchone()[0]
        cursor.execute('SELECT `Full_name`'
                + ' FROM `SEASON` WHERE `Part_of` = %s'
                + ' AND `Series_num` = %s;', [cmt[0], cmt[1]])
        season = cursor.fetchone()[0]
        comments.append({
            'anime' : anime,
            'season' : season,
            'snum' : cmt[1],
            'rating' : cmt[2],
            'text' : cmt[3],
            'datetime' : cmt[4],
            })

    return render_to_response('user.html', {
        'nav_users' : True,
        'user' : row,
        'comments' : comments,
        }, context_instance=RequestContext(request))


## -- Search -- ##
@login_required
@csrf_exempt
def search(request, t=None):
    keyword = request.GET['keyword']
    skeyword = keyword.replace('#', '##').replace('%', '#%').replace('_', '#_')
    skeyword = '%' + skeyword + '%'
    print skeyword
    cursor = connection.cursor()
    sql = '''
    SELECT `Id`, `Name`
    FROM `AUTHOR`
    WHERE `Name` LIKE %s ESCAPE '#';
    '''
    cursor.execute(sql, [skeyword])

    cols = [
        ('number','Id'),
        ('string','Name'),
    ]

    rows = cursor.fetchall()

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.author', args=[row[0]]))

    return render_to_response('table.html', {
        'keyword': keyword,
        'cols': cols,
        'rows': json.dumps(rows),
        'rowlinks' : json.dumps(rowlinks),
    }, context_instance=RequestContext(request))

## -- Animes -- ##
@login_required
def animes(request):
    cursor = connection.cursor()
    sql = '''
    SELECT `Title`, `Author`, `Web_address`, `Avg_rating`, `Id`
    FROM (
        SELECT `Id`, `Title`, `Authored_by`, `Web_address` FROM `ANIME`
    ) AS t1
    
    LEFT JOIN (
        SELECT `Id` AS `Authored_by`, `Name` AS `Author` FROM `AUTHOR`
    ) AS t2 USING(`Authored_by`)

    LEFT JOIN (
        SELECT `Commentee_anime` AS `Id`,
               AVG(`Rating`) AS `Avg_rating`
               FROM `COMMENTS_ON`
               GROUP BY `Id`
    ) AS t3 USING(`Id`);
    '''
    cursor.execute(sql)
    
    rows = cursor.fetchall()

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.anime', args=[row[4]]))

    rows = [ x[0:4] for x in rows ]
    
    cols = [
        ('string','Title'),
        ('string','Author'),
        ('string','Webpage'),
        ('number','Rating'),
    ]
    nav_list = [
            ['Anime View', None],
            ['Season View', reverse('animedbs.views.seasons')],
            None,
            ['Create Anime', reverse('animedbs.views.create_anime')],
            ]

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float('%.2f' % o)
            return super(DecimalEncoder, self).default(o)

    return render_to_response('table.html', {
        'nav_animes' : True,
        'pagetitle' : 'Animes',
        'cols' : cols,
        'rows' : json.dumps(rows, cls=DecimalEncoder),
        'nav_list' : nav_list,
        'rowlinks' : json.dumps(rowlinks),
        }, context_instance=RequestContext(request))

@login_required
def anime(request, aid):
    cursor = connection.cursor()
    sql = '''
    SELECT `Title`, `Author`, `Web_address`, `Avg_rating`
    FROM (
        SELECT `Id`, `Title`, `Authored_by`, `Web_address` FROM `ANIME`
    ) AS t1
    
    LEFT JOIN (
        SELECT `Id` AS `Authored_by`, `Name` AS `Author` FROM `AUTHOR`
    ) AS t2 USING(`Authored_by`)

    LEFT JOIN (
        SELECT `Commentee_anime` AS `Id`,
               AVG(`Rating`) AS `Avg_rating`
               FROM `COMMENTS_ON`
               GROUP BY `Id`
    ) AS t3 USING(`Id`)
    WHERE `Id` = %s;
    '''
    cursor.execute(sql, [aid])
    
    row = cursor.fetchone()

    if row is None:
        raise Http404()
    
    cols = [
        ('string','Title'),
        ('string','Author'),
        ('string','Webpage'),
        ('number','Rating'),
    ]

    sql = '''
    SELECT `Description`
    FROM `ANIME`
    WHERE `Id` = %s;
    '''
    cursor.execute(sql, [aid])

    desc = cursor.fetchone()[0]

    sql = '''
    SELECT `Full_name`, `Total_episodes`, `Release_year`, `Release_month`, `Title`, `Series_num`
    FROM `SEASON`, `ANIME`
    WHERE `Part_of` = %s AND `Id` = `Part_of`
    ORDER BY `Series_num`;
    '''

    cursor.execute(sql, [aid])

    rows = cursor.fetchall()
    seasons = []

    for season in rows:
        sql = '''
        SELECT `Nickname`, `Rating`, `Text`, `Datetime`, `Id`
        FROM `USER`, `COMMENTS_ON`
        WHERE `Commentee_anime` = %s
        AND `Commentee_season` = %s
        AND `Commenter` = `Id`;
        '''

        cursor.execute(sql, [aid, season[5]])

        crows = cursor.fetchall()
        comments = [ {
            'commenter' : x[0],
            'commenter_id' : x[4],
            'anime_id' : aid,
            'snum' : season[5],
            'rating' : x[1],
            'text' : x[2],
            'datetime' : x[3],
            } for x in crows ]

        season = {
                'full_name' : season[0],
                'snum' : season[5],
                'anime' : season[4],
                'episodes' : season[1],
                'year' : season[2],
                'month' : season[3],
                'comments' : comments,
                }
        seasons.append(season)

    sql = '''
    SELECT `Address`
    FROM `ANIME_IMAGE`
    WHERE `Anime_id` = %s;
    '''

    cursor.execute(sql, [aid])
    images = [ x[0] for x in cursor.fetchall() ]

    sql = '''
    SELECT C.`Name`, C.`Gender`, S.`Name`, C.`Description`
    FROM `CHARACTER` AS C, `SEIYU` AS S
    WHERE `Present_in` = %s AND S.`Id` = `Voiced_by`;
    '''

    cursor.execute(sql, [aid])

    crows = cursor.fetchall()
    characters = []
    for crow in crows:
        sql = '''
        SELECT `Address`
        FROM `CHARACTER_IMAGE`
        WHERE `Character_anime` = %s
        AND `Character_name` = %s;
        '''
        cursor.execute(sql, [aid, crow[0]])
        cimages = [ x[0] for x in cursor.fetchall() ]
        c = list(crow)
        c.append(cimages)
        characters.append(c)

    nav_list = [
            ['Edit Anime', reverse('animedbs.views.edit_anime', args=[aid])],
            ['Edit Images', reverse('animedbs.views.edit_anime_image', args=[aid])],
            ['Create Character', reverse('animedbs.views.create_anime_character', args=[aid])],
            ['Create Season', reverse('animedbs.views.create_season', args=[aid])],
            ]

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float('%.2f' % o)
            return super(DecimalEncoder, self).default(o)

    return render_to_response('anime.html', {
        'nav_animes' : True,
        'anime_id' : aid,
        'pagetitle' : row[0],
        'cols' : cols,
        'desc' : desc,
        'rows' : json.dumps([row], cls=DecimalEncoder),
        'nav_list' : nav_list,
        'seasons' : seasons,
        'images' : images,
        'characters' : characters,
        }, context_instance=RequestContext(request))

def edit_anime(request, aid):
    return create_entity(request, AnimeEntity, int(aid), delete=True)

def create_anime(request):
    return create_entity(request, AnimeEntity)

@login_required
def anime_images(request, aid):
    cursor = connection.cursor()
    sql = '''
    SELECT `Title`
    FROM `ANIME`
    WHERE `Id` = %s;
    '''
    cursor.execute(sql, [aid])
    
    row = cursor.fetchone()

    if row is None:
        raise Http404()

    anime = row[0]

    sql = '''
    SELECT `Address`
    FROM `ANIME_IMAGE`
    WHERE `Anime_id` = %s;
    '''

    cursor.execute(sql, [aid])
    rows = cursor.fetchall()

    cols = [
        ('string','Web_address'),
    ]
    nav_list = [
            ['Edit List', reverse('animedbs.views.edit_anime_image', args=[aid])],
            ['Back to Anime', reverse('animedbs.views.anime', args=[aid])],
            ]

    return render_to_response('table.html', {
        'nav_animes' : True,
        'pagetitle' : 'Images of %s' % anime,
        'cols' : cols,
        'rows' : json.dumps(rows),
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

def edit_anime_image(request, aid):
    return create_entity(request, AnimeImageEntity, int(aid))

def edit_anime_character(request, aid, cname):
    nav_list = [
            ['Edit Image', reverse('animedbs.views.edit_anime_character_image',
                args=[aid, cname])],
            ]
    return create_entity(request, CharacterEntity, [int(aid), cname], delete=True,
            nav_list = nav_list)

def create_anime_character(request, aid):
    return create_entity(request, CharacterEntity, [int(aid), None])

def edit_anime_character_image(request, aid, cname):
    return create_entity(request, AnimeCharacterImageEntity, [int(aid), cname])

@login_required
def seasons(request):
    cursor = connection.cursor()
    sql = '''
    SELECT `Full_name`, `Title`, `Series_num`, `Total_episodes`,
           `Release_year`, `Release_month`, `Avg_rating`, `Part_of`

    FROM `SEASON` AS t1

    LEFT JOIN (
        SELECT `Id` AS `Part_of`, `Title` FROM `ANIME`
    ) AS t2 USING (`Part_of`)

    LEFT JOIN (
        SELECT `Commentee_anime` AS `Part_of`,
               `Commentee_season` AS `Series_num`,
               AVG(`Rating`) AS `Avg_rating`
               FROM `COMMENTS_ON`
               GROUP BY `Part_of`, `Series_num`
    ) AS t3 USING(`Part_of`, `Series_num`);
    '''
    cursor.execute(sql)
    
    crows = cursor.fetchall()

    rows = [ list(x[:4]) + ['%d-%02d' % (x[4], x[5]), x[6]] for x in crows ]

    rowlinks = []
    for row in crows:
        rowlinks.append(reverse('animedbs.views.season', args=[row[7], row[2]]))
    
    cols = [
        ('string','Full Name'),
        ('string','Anime'),
        ('number','Season'),
        ('number','Total Episodes'),
        ('string','Release Time'),
        ('number','Rating'),
    ]

    nav_list = [
            ['Anime View', reverse('animedbs.views.animes')],
            ['Season View', None],
            ]


    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float('%.2f' % o)
            return super(DecimalEncoder, self).default(o)

    return render_to_response('table.html', {
        'nav_animes' : True,
        'pagetitle' : 'Animes',
        'cols' : cols,
        'rows' : json.dumps(rows, cls=DecimalEncoder),
        'nav_list' : nav_list,
        'rowlinks' : json.dumps(rowlinks),
        }, context_instance=RequestContext(request))

@login_required
def season(request, aid, snum):

    cursor = connection.cursor()

    sql = '''
    SELECT `Full_name`, `Total_episodes`, `Release_year`, `Release_month`, `Title`
    FROM `SEASON`, `ANIME`
    WHERE `Part_of` = %s AND `Series_num` = %s AND `Id` = `Part_of`;
    '''

    cursor.execute(sql, [aid, snum])

    row = cursor.fetchone()

    if row is None:
        raise Http404()


    sql = '''
    SELECT `Nickname`, `Rating`, `Text`, `Datetime`, `Id`
    FROM `USER`, `COMMENTS_ON`
    WHERE `Commentee_anime` = %s
    AND `Commentee_season` = %s
    AND `Commenter` = `Id`;
    '''

    cursor.execute(sql, [aid, snum])

    rows = cursor.fetchall()
    comments = [ {
        'commenter' : x[0],
        'commenter_id' : x[4],
        'anime_id' : aid,
        'snum' : snum,
        'rating' : x[1],
        'text' : x[2],
        'datetime' : x[3],
        } for x in rows ]

    nav_list = [
            ['Rate it!', reverse('animedbs.views.comment', args=[aid, snum])],
            ['Edit', reverse('animedbs.views.edit_season', args=[aid, snum])],
            ]

    return render_to_response('season.html', {
        'nav_animes' : True,
        'full_name' : row[0],
        'snum' : snum,
        'anime' : row[4],
        'episodes' : row[1],
        'year' : row[2],
        'month' : row[3],
        'comments' : comments,
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

def edit_season(request, eid, snum):
    return create_entity(request, SeasonEntity, [int(eid), int(snum)], delete=True)

def create_season(request, eid):
    return create_entity(request, SeasonEntity, [int(eid), None])

## -- Songs -- ##
@login_required
def songs(request):
    cursor = connection.cursor()
    sql = '''
    SELECT `Id`, `Title`, `Seiyu_name`, `Anime_name`, `Anime_series`, `Type`
    FROM (
        SELECT
            `Id`,
            `Title`,
            `Singed_by` AS `Seiyu_id`,
            `Featured_in_aid` AS `Anime_id`,
            `Featured_in_snum` AS `Anime_series`,
            `Type`
        FROM `SONG`
    ) AS t1
        
    LEFT JOIN (
        SELECT `Title` AS `Anime_name`, `Id` AS `Anime_id` FROM `ANIME`
    ) AS t2 USING (`Anime_id`)

    LEFT JOIN (
        SELECT `Name` AS `Seiyu_name`, `Id` AS `Seiyu_id` FROM `SEIYU`
    ) AS t3 USING (`Seiyu_id`);
    '''
    cursor.execute(sql)

    rows = cursor.fetchall()
    
    cols = [
        ('number', 'Id'),
        ('string', 'Title'),
        ('string', 'Singer'),
        ('string', 'Featured Anime'),
        ('number', 'Featured Season'),
        ('string', 'Type'),
    ]

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.song', args=[row[0]]))

    nav_list = [['Create Song', reverse('animedbs.views.create_song')],]

    return render_to_response('table.html', {
        'nav_songs' : True,
        'pagetitle' : 'Songs',
        'cols' : cols,
        'rows' : json.dumps(rows),
        'rowlinks' : json.dumps(rowlinks),
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

def song(request, sid):
    cursor = connection.cursor()
    sql = '''
    SELECT `Id`, `Title`, `Seiyu_name`, `Anime_name`, `Anime_series`, `Type`
    FROM (
        SELECT
            `Id`,
            `Title`,
            `Singed_by` AS `Seiyu_id`,
            `Featured_in_aid` AS `Anime_id`,
            `Featured_in_snum` AS `Anime_series`,
            `Type`
        FROM `SONG` WHERE `Id` = %s
    ) AS t1
        
    LEFT JOIN (
        SELECT `Title` AS `Anime_name`, `Id` AS `Anime_id` FROM `ANIME`
    ) AS t2 USING (`Anime_id`)

    LEFT JOIN (
        SELECT `Name` AS `Seiyu_name`, `Id` AS `Seiyu_id` FROM `SEIYU`
    ) AS t3 USING (`Seiyu_id`);
    '''
    cursor.execute(sql, [sid])

    row = cursor.fetchone()
    if row is None:
        raise Http404()
    
    cols = [
        ('number', 'Id'),
        ('string', 'Title'),
        ('string', 'Singer'),
        ('string', 'Featured Anime'),
        ('number', 'Featured Season'),
        ('string', 'Type'),
    ]

    sql = '''
    SELECT `Lyrics`
    FROM `SONG` WHERE `Id` = %s;
    '''
    cursor.execute(sql, [sid])

    lyrics = cursor.fetchone()[0]

    nav_list = [['Edit Song', reverse('animedbs.views.edit_song',
        args=[sid])],]

    return render_to_response('song.html', {
        'nav_songs' : True,
        'pagetitle' : row[1],
        'cols' : cols,
        'rows' : json.dumps([row]),
        'lyrics' : lyrics,
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

def edit_song(request, eid):
    return create_entity(request, SongEntity, int(eid), delete=True)

def create_song(request):
    return create_entity(request, SongEntity)

## -- Authors -- ##
@login_required
def authors(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Name` FROM `AUTHOR`;')

    rows = cursor.fetchall()

    cols = [
        ('number','Id'),
        ('string','Name'),
    ]

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.author', args=[row[0]]))

    return render_to_response('table.html', {
        'nav_authors' : True,
        'pagetitle' : 'Authors',
        'cols' : cols,
        'rows' : json.dumps(rows),
        'rowlinks' : json.dumps(rowlinks),
        }, context_instance=RequestContext(request))

@login_required
def author(request, arid):
    cursor = connection.cursor()
    cursor.execute('SELECT `Name`, `Description`'
            + ' FROM `AUTHOR` WHERE `Id` = %s;', [arid])
    row = cursor.fetchone()
    if row is None:
        raise Http404()

    author_list = []

    cursor.execute('SELECT `Title`'
            + ' FROM `ANIME` WHERE `Authored_by` = %s;',
            [arid])
    author_list.append({
        'id' : arid,
        'name' : row[0],
        'desc' : row[1],
        'anime_list' : cursor.fetchall(),
        })

    nav_list = [
            ['Edit Author', reverse('animedbs.views.edit_author', args=[arid])],
            ]
    return render_to_response('authors.html', {
        'nav_authors' : True,
        'author_list' : author_list,
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

def edit_author(request, arid):
    return create_entity(request, AuthorEntity, int(arid))

## -- Seiyus -- ##
@login_required
def seiyus(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Name`, `Gender`, `Birthday` FROM `SEIYU`;')

    rows = cursor.fetchall()

    cols = [
        ('number','Id'),
        ('string','Name'),
        ('string','Gender'),
        ('string','Birthday'),
    ]

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.seiyu', args=[row[0]]))

    nav_list = [['Create Seiyu', reverse('animedbs.views.create_seiyu')],]

    class DateEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime.date):
                return o.strftime('%Y-%m-%d')
            return super(DateEncoder, self).default(o)

    return render_to_response('table.html', {
        'nav_seiyus' : True,
        'pagetitle' : 'Seiyus',
        'cols' : cols,
        'rows' : json.dumps(rows, cls=DateEncoder),
        'rowlinks' : json.dumps(rowlinks),
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))

@login_required
def seiyu(request, sid):
    cursor = connection.cursor()
    cursor.execute('SELECT *'
            + ' FROM `SEIYU` WHERE `Id` = %s;', [sid])
    row = cursor.fetchone()
    cursor.execute('SELECT `Title`'
            + ' FROM `CHARACTER`, `ANIME`'
            + ' WHERE `Voiced_by` = %s'
            + ' AND `Present_in` = `ANIME`.`Id`;', [sid])
    animes = cursor.fetchall()
    cursor.execute('SELECT `Name`'
            + ' FROM `CHARACTER` WHERE `Voiced_by` = %s;', [sid])
    characters = cursor.fetchall()
    cursor.execute('SELECT `Title`'
            + ' FROM `SONG` WHERE `Singed_by` = %s;', [sid])
    songs = cursor.fetchall()
    thead = ['Id',
            'Name',
            'Gender',
            'Birthday',
            'Description'
            ]
    nav_list = [
            ['Edit', reverse('animedbs.views.edit_seiyu', args=[sid])],
            ]
    return render_to_response('seiyu.html', {
        'nav_seiyus' : True,
        'row' : row,
        'animes' : animes,
        'characters' : characters,
        'songs' : songs,
        'table_header' : thead,
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))


def create_seiyu(request):
    return create_entity(request, SeiyuEntity)

def edit_seiyu(request, eid):
    return create_entity(request, SeiyuEntity, int(eid))


@login_required
def create_entity(request, Entity, eid=None, delete=False, nav_list=None):
    entity = Entity()
    if eid:
        entity.setId(eid)
    if request.method == 'POST':
        entity.parse(request.POST)
        if 'delete' in request.POST:
            entity.delete()
            return entity.redirect()
        if entity.is_valid():
            entity.update()
            if entity.redirect():
                return entity.redirect()
    return render_to_response('form.html', {
        entity.nav_name() : True,
        'pagetitle' : entity.title(),
        'form' : entity.form(),
        'delete' : delete,
        'nav_list' : nav_list,
        }, context_instance=RequestContext(request))
