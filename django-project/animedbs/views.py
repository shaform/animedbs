from django.db import connection, transaction
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from animedbs.forms import LoginForm

def index(request):
    # msg = "Hello %s"
    # return HttpResponse(msg)
    pass

def login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cursor = connection.cursor()
            # check if account exists
            email = form.cleaned_data['email']
            cursor.execute("SELECT `Id` FROM `USER` WHERE Email = %s", [email])
            row = cursor.fetchone()
            if row is None:
                return HttpResponse("No this man %s" % email)
            # cursor.execute("INSERT IGNORE INTO `users`\n\"")
            else:
                return HttpResponse("Yes this man")
                # request.session.
            # transaction.commit_unless_managed()
        else:
            return render_to_response('home.html', {
                'form' : form,
                }, context_instance=RequestContext(request))
    else:
        return render_to_response('home.html', {
            'form' : form,
            }, context_instance=RequestContext(request))

def home(request):
    if request.session.get('user_id', 0) == 0:
        return login(request)
    else:
        return index(request)
