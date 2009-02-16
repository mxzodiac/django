"""
Specialized generic views for viewing models.
"""

from django.views.generic2.base import Option, ListView

class ModelListView(ListView):
    queryset = Option()
    
    def get_items(self, request, page):
        """
        Get the items -- queryset -- for this view.
        """
        queryset = self.queryset(request, None)
        queryset = queryset._clone()
        if queryset is None:
            raise ImproperlyConfigured("'%s' must define 'queryset'" % self.__class__.__name__)
        return self.paginate_items(request, items, queryset))
        
    def get_template_names(self, request, queryset):
        names = super(ModelListView, self).get_template_names(request, queryset)
        info = {
            'app'  : queryset.model._meta.app_label,
            'model': queryset.model._meta.object_name.lower(),
        }
        names.append('%(app)s/%(model)s_list.html' % info)
        return names
        