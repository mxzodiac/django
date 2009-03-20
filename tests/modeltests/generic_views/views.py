from models import Author, Book
from django.views.generic2 import ListView, DetailView

class DictList(ListView):
    """A ListView that doesn't use a model."""
    items = [
        {'first': 'John', 'last': 'Lennon'},
        {'last': 'Yoko',  'last': 'Ono'}
    ]
    template_name = 'generic_views/list.html'

class AuthorList(ListView):
    queryset = Author.objects.all()
    template_name = 'generic_views/list.html'
    
class AuthorDetail(DetailView):
    queryset = Author.objects.all()
    
class ObjectDetail(DetailView):
    template_name = 'generic_views/detail.html'
    def get_object(self, request, **kwargs):
        return {'foo': 'bar'}
        