import models
from django.views.generic2 import ListView

class DictList(ListView):
    """A ListView that doesn't use a model."""
    items = [
        {'first': 'John', 'last': 'Lennon'},
        {'last': 'Yoko',  'last': 'Ono'}
    ]
    template_name = 'generic_views/list.html'

class AuthorList(ListView):
    queryset = models.Author.objects.all()
    template_name = 'generic_views/list.html'
    
