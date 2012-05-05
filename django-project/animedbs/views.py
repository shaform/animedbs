from django.db import connection, transaction
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm
from animedbs.forms import ProfileForm


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

    return render_to_response('home.html', {
        'form' : form,
        }, context_instance=RequestContext(request))

def home(request):
    if 'user_id' not in request.session:
        return login(request)
    else:
        return index(request)



## -- Users -- ##

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
        'form' : form,
        }, context_instance=RequestContext(request))

def users(request):
    cursor = connection.cursor()
    cursor.execute('SELECT `Id`, `Email`, `Nickname`, `Gender`'
            + ' FROM `USER`;')
    return render_to_response('users.html', {
        'user_list' : cursor.fetchall(),
        }, context_instance=RequestContext(request))


## -- Search -- ##
## -- Animes -- ##
## -- Songs -- ##

