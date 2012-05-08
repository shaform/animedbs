import json
from django.db import connection, transaction
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm
from animedbs.forms import ProfileForm
from animedbs.forms import SeiyuEntity

def login_required(function):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('animedbs.views.profile')
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
    cursor.execute('SELECT `Id`, `Email`, `Nickname`, `Gender`'
            + ' FROM `USER`;')
    return render_to_response('users.html', {
        'user_list' : cursor.fetchall(),
        'pagetitle' : 'Users',
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
    return render_to_response('temp.html', {
        #'user_list' : cursor.fetchall(),
        'keyword': keyword,
        'tbl': json.dumps(cursor.fetchall()),
        'cols': [('number','ID'),('string', 'Email'),('string', 'Name'),('string', 'Gender')],
    }, context_instance=RequestContext(request))


## -- Animes -- ##
@login_required
def animes(request):
    cursor = connection.cursor()
    cursor.execute('SELECT *'
            + ' FROM `ANIME`;')
    return render_to_response('temp.html', {
        'user_list' : cursor.fetchall(),
        }, context_instance=RequestContext(request))


## -- Songs -- ##
@login_required
def songs(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Title`, `Singed_by`,'
            + '`Featured_in_aid`, `Featured_in_snum`,'
            + ' `Type` FROM `SONG`;')
    rows = cursor.fetchall()
    songs = []
    for song in rows:
        cursor.execute('SELECT `Title`'
                + ' FROM `ANIME` WHERE `Id` = %s;', [song[3]])
        anime = cursor.fetchone()[0]
        cursor.execute('SELECT `Name`'
                + ' FROM `SEIYU` WHERE `Id` = %s;', [song[2]])
        seiyu = cursor.fetchone()[0]
        songs.append([song[0], song[1], seiyu, anime, song[4], song[5]])
    header = ['Id', 'Title', 'Sing_by',
            'Featured anime', 'Featured season', 'Type']
    return render_to_response('temp.html', {
        'user_list' : songs,
        'table_header' : header,
        }, context_instance=RequestContext(request))

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
        'author_list' : author_list,
        }, context_instance=RequestContext(request))


## -- Seiyus -- ##
@login_required
def seiyus(request):
    cursor = connection.cursor()
    cursor.execute('SELECT *'
            + ' FROM `SEIYU`;')
    return render_to_response('seiyus.html', {
        'user_list' : cursor.fetchall(),
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
def create_entity(request, Entity, eid=None):
    entity = Entity()
    if eid:
        entity.setId(eid)
    if request.method == 'POST':
        entity.parse(request.POST)
        if entity.is_valid():
            entity.update()
            if entity.redirect():
                return entity.redirect()
    return render_to_response('form.html', {
        'pagetitle' : entity.title(),
        'form' : entity.form(),
        }, context_instance=RequestContext(request))
