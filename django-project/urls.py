from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'^animedbs/', include('animedbs.urls')),
)
