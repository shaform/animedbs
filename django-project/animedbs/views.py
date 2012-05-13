import datetime
import decimal
import json
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm
from animedbs.forms import ProfileForm
from animedbs.forms import SeiyuEntity
from animedbs.forms import SongEntity

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
def search(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Email`, `Nickname`, `Gender`'
            + ' FROM `USER`;')
    keyword = request.GET['keyword']
    return render_to_response('table.html', {
        'keyword': keyword,
        'cols': [('number','ID'),('string', 'Email'),('string', 'Name'),
                ('string', 'Gender')],
        'rows': json.dumps(cursor.fetchall()),
    }, context_instance=RequestContext(request))


## -- Animes -- ##
@login_required
def animes(request):
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
    ) AS t3 USING(`Id`);
    '''
    cursor.execute(sql)
    
    rows = cursor.fetchall()
    
    cols = [
        ('string','Title'),
        ('string','Author'),
        ('string','Webpage'),
        ('number','Rating'),
    ]
    nav_list = [
            ['Anime View', None],
            ['Season View', reverse('animedbs.views.seasons')],
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
        }, context_instance=RequestContext(request))

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
        'pagetitle' : 'Seasons',
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
    SELECT `Nickname`, `Rating`, `Text`, `Datetime`
    FROM `USER`, `COMMENTS_ON`
    WHERE `Commentee_anime` = %s
    AND `Commentee_season` = %s
    AND `Commenter` = `Id`;
    '''

    cursor.execute(sql, [aid, snum])

    rows = cursor.fetchall()
    comments = [ {
        'commenter' : x[0],
        'rating' : x[1],
        'text' : x[2],
        'datetime' : x[3],
        } for x in rows ]

    return render_to_response('season.html', {
        'full_name' : row[0],
        'snum' : snum,
        'anime' : row[4],
        'episodes' : row[1],
        'year' : row[2],
        'month' : row[3],
        'comments' : comments,
        }, context_instance=RequestContext(request))

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
        rowlinks.append(reverse('animedbs.views.edit_song', args=[row[0]]))

    nav_list = [['new', reverse('animedbs.views.create_song')],]

    return render_to_response('table.html', {
        'nav_songs' : True,
        'pagetitle' : 'Songs',
        'cols' : cols,
        'rows' : json.dumps(rows),
        'rowlinks' : json.dumps(rowlinks),
        'nav_list' : nav_list,
        #'db_debug' : sql,
        }, context_instance=RequestContext(request))

def edit_song(request, eid):
    return create_entity(request, SongEntity, eid, delete=True)

def create_song(request):
    return create_entity(request, SongEntity)

## -- Authors -- ##
@login_required
def authors(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Name`, `Description`'
            + ' FROM `AUTHOR`;')
    rows = cursor.fetchall()
    author_list = []

    for row in rows:
        cursor.execute('SELECT `Title`'
                + ' FROM `ANIME` WHERE `Authored_by` = %s;',
                [row[0]])
        author_list.append({
            'id' : row[0],
            'name' : row[1],
            'desc' : row[2],
            'anime_list' : cursor.fetchall(),
            })
    return render_to_response('authors.html', {
        'nav_authors' : True,
        'author_list' : author_list,
        }, context_instance=RequestContext(request))


## -- Seiyus -- ##
@login_required
def seiyus(request):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM `SEIYU`;')

    rows = cursor.fetchall()

    cols = [
        ('number','Id'),
        ('string','Name'),
        ('string','Gender'),
        ('string','Birthday'),
        ('string','Description'),
    ]

    rowlinks = []
    for row in rows:
        rowlinks.append(reverse('animedbs.views.seiyu', args=[row[0]]))

    nav_list = [['new', reverse('animedbs.views.create_seiyu')],]

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
    return render_to_response('seiyu.html', {
        'nav_seiyus' : True,
        'row' : row,
        'animes' : animes,
        'characters' : characters,
        'songs' : songs,
        }, context_instance=RequestContext(request))

def create_seiyu(request):
    return create_entity(request, SeiyuEntity)

def edit_seiyu(request, eid):
    return create_entity(request, SeiyuEntity, eid)


@login_required
def create_entity(request, Entity, eid=None, delete=False):
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
        }, context_instance=RequestContext(request))

