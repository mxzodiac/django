from models import Author, Book
from django.views import generic2 as generic

class DictList(generic.ListView):
    """A ListView that doesn't use a model."""
    items = [
        {'first': 'John', 'last': 'Lennon'},
        {'last': 'Yoko',  'last': 'Ono'}
    ]
    template_name = 'generic_views/list.html'

class AuthorList(generic.ListView):
    queryset = Author.objects.all()
    template_name = 'generic_views/list.html'
    
class AuthorDetail(generic.DetailView):
    queryset = Author.objects.all()
    
class ObjectDetail(generic.DetailView):
    template_name = 'generic_views/detail.html'
    def get_object(self, request, **kwargs):
        return {'foo': 'bar'}

class BookArchive(generic.ArchiveView):
    queryset = Book.objects.all()
    date_field = 'pubdate'

class BookYearArchive(generic.YearView):
    queryset = Book.objects.all()
    date_field = 'pubdate'
    
class BookMonthArchive(generic.MonthView):
    queryset = Book.objects.all()
    date_field = 'pubdate'