from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
        url(r'', include('animedbs.urls')),
)
