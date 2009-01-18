from django.db import models

class Author(models.Model):
   name = models.CharField(max_length=100)
   slug = models.SlugField()

   def __unicode__(self):
       return self.name

class Book(models.Model):
   name = models.CharField(max_length=300)
   pages = models.IntegerField()
   authors = models.ManyToManyField(Author)
   pubdate = models.DateField()
   
   def __unicode__(self):
       return self.name

