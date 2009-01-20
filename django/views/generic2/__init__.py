import re
import django.template.loader
from django import template
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.xheaders import populate_xheaders
from django.http import HttpResponse, Http404

class DetailView(object):
    """
    Remember: caching on self is RIGHT OUT.
    """
    context_processors = None
    mimetype = None
    queryset = None
    slug_field = None
    template_loader = None
    template_object_name = None
    template_name = None
    template_name_field = None
    template_names = None
    
    def get_queryset(self, request):
        """
        Get the queryset for the request.
        """
        if self.queryset is None:
            raise ImproperlyConfigured("ListDetailView must be given a queryset. "\
                                       "Define self.queryset, or self.get_queryset().")
        return self.queryset
        
    def get_object(self, request, pk, slug):
        qs = self.get_queryset(request)
        if pk:
            qs = qs.filter(pk=pk)
        elif slug:
            slug_field = self.slug_field or 'slug'
            qs = qs.filter(**{slug_field: slug})
        else:
            raise AttributeError("Generic detail view must be called with "\
                                 "either an object id or a slug.")
    
        try:
            return qs.get()
        except ObjectDoesNotExist:
            raise Http404("No %s found matching the query" % \
                          (qs.model._meta.verbose_name))
    
    def get_template(self, request, obj):
        """
        Get a Template object for the given request.
        """
        names = self.get_template_names(request, obj)
        return self.load_template(request, obj, names)
        
    def get_template_names(self, request, obj):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """
        names = []
        
        # If self.template_name_field is set, grab the value of the field
        # of that name from the object; this is the most specific template
        # name, if given.
        if self.template_name_field:
            name = getattr(obj, self.template_name_field, None)
            if name:
                names.append(name)
                
        # Next, try self.template_names
        names.extend(self.template_names or [])
                
        # Now fall down to self.template_name.
        if self.template_name:
            names.append(self.template_name)
            
        # Finally, the least-specific option is the default 
        # <app>/<model>_detail.html.
        names.append("%s/%s_detail.html" % (obj._meta.app_label, 
                                            obj._meta.object_name.lower()))
            
        return names
        
    def load_template(self, request, obj, names):
        """
        Load a template, using self.template_loader or the default.
        """
        loader = self.template_loader or django.template.loader
        return loader.select_template(names)
        
    def get_context(self, request, obj):
        """
        Get the context. Must return a Context (or subclass) instance.
        """
        nicename = self.template_object_name or \
                   re.sub('[^a-zA-Z0-9]+', '_', obj._meta.verbose_name.lower())
                   
        context = template.RequestContext(request, {
            "object": obj,
            nicename: obj,
        }, self.get_context_processors(request, obj))
        
        return context
    
    def get_context_processors(self, request, obj):
        """
        Get the context processors.
        """
        return self.context_processors
        
    def get_mimetype(self, request, obj):
        """
        Get the mimetype for the response.
        """
        return self.mimetype or 'text/html'
                
    def __call__(self, request, pk=None, slug=None, object_id=None):
        """
        The view.
        """
        pk = pk or object_id
        obj = self.get_object(request, pk, slug)
        template = self.get_template(request, obj)
        context = self.get_context(request, obj)
        response = HttpResponse(template.render(context), 
                                mimetype=self.get_mimetype(request, obj))
        populate_xheaders(request, response, obj.__class__, obj.pk)
        return response
