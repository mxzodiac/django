import views
from django.views.generic2 import GenericView
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^list/dict/$',
        views.DictList()),
    
    (r'^list/authors/$',
        views.AuthorList()),
    
    (r'^list/authors/paginated/$',
        views.AuthorList(paginate_by=30)),
    
    (r'^list/authors/paginated/(?P<page>\d+)/$',
        views.AuthorList(paginate_by=30)),
    
    (r'^list/authors/notempty/$',
        views.AuthorList(allow_empty=False)),
    
    (r'^list/authors/template_object_name/$',
        views.AuthorList(template_object_name='author')),
        
    (r'^detail/obj/$',
        views.ObjectDetail()),
        
    (r'^detail/author/(?P<pk>\d+)/$',
        views.AuthorDetail()),
        
    (r'^detail/author/byslug/(?P<slug>[\w-]+)/$',
        views.AuthorDetail()),
        
    (r'^detail/author/invalid/$',
        views.AuthorDetail()),
    
)