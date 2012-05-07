from django.db import connection, transaction
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm
from animedbs.forms import ProfileForm

def login_required(function):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if 'user_id' not in request.session:
                return redirect('/')
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
    return redirect('/')

def register(request, email):
    cursor = connection.cursor()

    cursor.execute('INSERT INTO `USER` (Email, Nickname, Gender)'
            + 'VALUES (%s, %s, %s);', [email, 'Guest', 'other'])
    transaction.commit_unless_managed()

    cursor.execute('SELECT `Id` FROM `USER` WHERE Email = %s', [email])
    request.session['user_id'] = cursor.fetchone()[0]

    return redirect('/profile')

def login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cursor = connection.cursor()

            # check if account exists
            email = form.cleaned_data['email']
            cursor.execute('SELECT `Id` FROM `USER` WHERE Email = %s', [email])
            row = cursor.fetchone()

            if row is None:
                return register(request, email)
            else:
                request.session['user_id'] = row[0]
                return index(request)

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
        return redirect('/')

    cursor = connection.cursor()

    user_id = request.session['user_id']
    cursor.execute('SELECT `Email`, `Nickname`, `Gender`'
            + ' FROM `USER` WHERE `Id` = %s', [user_id])
    row = cursor.fetchone()
    email = row[0]

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
            return redirect('/profile')

    return render_to_response('profile.html', {
        'email' : email,
        'username' : row[1],
        'form' : form,
        }, context_instance=RequestContext(request))


@login_required
def users(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Email`, `Nickname`, `Gender`'
            + ' FROM `USER`;')
    return render_to_response('users.html', {
        'user_list' : cursor.fetchall(),
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
        'user_list' : cursor.fetchall(),
        'keyword': keyword,
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
    cursor.execute('SELECT *'
            + ' FROM `SONG`;')
    return render_to_response('temp.html', {
        'user_list' : cursor.fetchall(),
        }, context_instance=RequestContext(request))


## -- Authors -- ##
@login_required
def authors(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Name`, `Description`'
            + ' FROM `AUTHOR`;')
    return render_to_response('temp.html', {
        'user_list' : cursor.fetchall(),
        }, context_instance=RequestContext(request))


## -- Seiyus -- ##
@login_required
def seiyus(request):
    cursor = connection.cursor()
    cursor.execute('SELECT *'
            + ' FROM `SEIYU`;')
    return render_to_response('temp.html', {
        'user_list' : cursor.fetchall(),
        }, context_instance=RequestContext(request))

