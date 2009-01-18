import views
from django.conf.urls.defaults import *

urlpatterns = patterns('', 
    (r'^books/(?P<pk>\d+)/$', views.BookDetail()),
)