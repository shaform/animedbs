from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^$', 'animedbs.views.home'),
        url(r'^logout/$', 'animedbs.views.logout'),
        url(r'^user/$', 'animedbs.views.users'),
        url(r'^profile/$', 'animedbs.views.profile'),
        url(r'^author/$', 'animedbs.views.authors'),
        url(r'^anime/$', 'animedbs.views.animes'),
        url(r'^seiyu/$', 'animedbs.views.seiyus'),
        url(r'^song/$', 'animedbs.views.songs'),
        url(r'^search/$', 'animedbs.views.search'),
)
