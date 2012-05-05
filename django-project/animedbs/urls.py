from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^$', 'animedbs.views.home'),
        url(r'^logout$', 'animedbs.views.logout'),
        url(r'^users$', 'animedbs.views.users'),
        url(r'^profile$', 'animedbs.views.profile'),
        #url(r'^authors$', 'animedbs.views.authors'),
)
