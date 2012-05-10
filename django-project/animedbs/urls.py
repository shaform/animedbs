from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^$', 'animedbs.views.home'),
        url(r'^logout/$', 'animedbs.views.logout'),
        url(r'^user/$', 'animedbs.views.users'),
        url(r'^user/(\d+)/$', 'animedbs.views.user'),
        url(r'^profile/$', 'animedbs.views.profile'),
        url(r'^author/$', 'animedbs.views.authors'),
        url(r'^anime/$', 'animedbs.views.animes'),
        url(r'^season/$', 'animedbs.views.seasons'),
        url(r'^seiyu/$', 'animedbs.views.seiyus'),
        url(r'^seiyu/new/$', 'animedbs.views.create_seiyu'),
        url(r'^seiyu/(\d+)/$', 'animedbs.views.seiyu'),
        url(r'^seiyu/(\d+)/edit/$', 'animedbs.views.edit_seiyu'),
        url(r'^song/$', 'animedbs.views.songs'),
        url(r'^song/new/$', 'animedbs.views.create_song'),
        url(r'^song/(\d+)/$', 'animedbs.views.edit_song'),
        url(r'^song/(\d+)/edit/$', 'animedbs.views.edit_song'),
        url(r'^search/$', 'animedbs.views.search'),
)
