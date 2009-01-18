from django.test import TestCase
import models

class DetailViewTest(TestCase):
    fixtures = ['generic-views-test-data.json']
    urls = 'modeltests.generic_views.urls'
    
    def test_get_by_id(self):
        r = self.client.get('/books/1/')
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'generic_views/book_detail.html')
        
        # The old-style without template_object_name
        self.assertEqual(r.context['object'], models.Book.objects.get(pk=1))  
        
        # The new-style, guessed name,
        self.assertEqual(r.context['book'], models.Book.objects.get(pk=1))
