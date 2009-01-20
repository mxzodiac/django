from django.views.generic2 import DetailView
import models

class BookDetail(DetailView):
    queryset = models.Book.objects.all()