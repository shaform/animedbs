from django.db import connection, transaction
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm


#### -- Home Page -- ####
def index(request):
    msg = 'Hello %d' % request.session['user_id']
    return HttpResponse(msg)

def logout(request):
    for key in request.session.keys():
        del request.session[key]
    return redirect('/')

def register(request, email):
    cursor = connection.cursor()

    cursor.execute('INSERT INTO `USER` (Email, Nickname, Gender)'
            + 'VALUES (%s, %s, %s);', [email, 'Nickname', 'other'])
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
    return HttpResponse()
    pass

def users(request):
    cursor = connection.cursor()
    cursor.execute('SELECT Id, Email, Nickname Gender'
            + 'FROM `USER`;')

    return render_to_response('profile.html', {
        'form' : form,
        }, context_instance=RequestContext(request))


## -- Search -- ##
## -- Animes -- ##
## -- Songs -- ##

