from django.core.exceptions import ImproperlyConfigured

class Option(object):
    """
    An "option" for a generic view that may be filled by an attribute or a
    function. Really just a marker for the metaclass and a placeholder for the
    default values.
    """
    def __init__(self, default=None):
        self.default = default
        
        # Filled in by the metaclass
        self.name = None

class OptionsMetaclass(type):
    """
    Metaclass that supports the definition of configuration options by
    swizziling any ``GenericViewOption`` attributes into an ``__options__``
    dictionary.
    """    
    def __new__(cls, name, bases, attrs):        
        # Gather options set by any parent classes.
        options = {}
        for parent in bases:
            options.update(getattr(parent, '__options__', {})
            
        # If any attributes on the class are options, add them to the dict of
        # options and remove them from the list of attrs for this class.
        for attr, value in attrs.items():
            if isinstance(value, GenericViewOption):
                option = attrs.pop(attr)
                option.name = attr
                options[option.name] = option
                
        # Save the options as cls.__options__
        attrs['__options__'] = options
        
        return super(OptionsMetaclass, cls).__new__(cls, name, bases, attrs)
    
class GenericView(object):
    """
    Parent class for all generic views. Handles the wrapping of options defined
    as attributes, and also defines the options and defaults shared by all
    generic views.
    """
    __metaclass__ = OptionsMetaclass
    
    # Options that all generic views take
    context_processors   = Option()
    mimetype             = Option(default="text/html")
    template_loader      = Option()
    template_name        = Option()
    
    def __getattribute__(self, name):
        # Remember: we can't use ``object.whatever`` in here; that'll lead to
        # an infinite loop. We must use the parent classes' __getattribute__
        superget = super(GenericView, self).__getattribute__
        options = superget('__options__')
        
        # We only want to handle options.
        if name not in options:
            return superget(name)
                
        # Try to get a value from this class, and fall back on # the default.
        try:
            value = superget(options[name])
        except AttributeError:
            value = options[name].default

        # If this is a callable, return it. Otherwise, convert the attribute
        # into a callable by calling self.__wrap__.
        if callable(value):
            return value
        else:
            return superget('__wrap__')(value)
            
    def __wrap__(self, value):
        """
        The default wrapper function. The signature of most generic view option
        callbacks is (request, some_object).
        """
        return lambda request, obj: value
        
    def get_template(self, request, obj):
        """
        Get a Template object for the given request.
        """
        names = self.get_template_names(request, obj)
        if not names:
            raise ImproperlyConfigured("'%s' must provide template_name." % self.__class__.__name__)
        return self.load_template(request, obj, names)

    def get_template_names(self, request, obj):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """                        
        # Try self.template_name; it could be a string or list.
        names = self.template_name(request, obj)
        if names is None:
            return []
        elif isinstance(tns, basestring):
            return [names]
        else:
            return names
            
    def load_template(self, request, obj, names):
        """
        Load a template, using self.template_loader or the default.
        """
        import django.template.loader
        loader = self.template_loader(request, obj) or django.template.loader
        return loader.select_template(names)
        
    def get_context(self, request, obj):
        """
        Get the context. Must return a Context (or subclass) instance.
        """
        processors = self.context_processors(request, obj)
        return template.RequestContext(request, {}, processors)
    
class ListView(GenericView):
    """
    Render some list of objects. This view doesn't know anything about models;
    for that see ModelListView.
    """
    
    items                = Option()
    paginate_by          = Option()
    allow_empty          = Option(default=True)
    template_object_name = Option(default='object')
    
    def __call__(self, request, page=None):
        paginator, page items = self.get_items(request, page)
        template = self.get_template(request, items)
        context = self.get_context(request, items, paginator, page)
        mimetype = self.mimetype(request, items)
        return HttpResponse(template.render(context), mimetype=mimetype)

    def get_items(self, request, page):
        """
        Get the list of items for this view.
        """
        items = self.items(request, None)
        if items is None:
            raise ImproperlyConfigured("'%s' must define 'items'" % self.__class__.__name__)
        return self.paginate_items(request, items, page))
            
    def paginate_items(self, request, items, page):
        """
        Paginate the list of items, if needed.
        """
        paginate_by = self.paginate_by(request, items)
        allow_empty = self.allow_empty(request, items)        
        if not paginate_by:
            if not allow_empty and len(items) == 0:
                raise Http404("Empty list and '%s.allow_empty' is False." % self.__class__.__name__)
            return (None, None, items)
        
        paginator = Paginator(queryset, paginate_by, allow_empty_first_page=allow_empty)
        page = page or request.GET.get('page', 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404("Page is not 'last', nor can it be converted to an int.")
        try:
            return paginator.page(page_number)
        except InvalidPage:
            raise Http404('Invalid page (%s)' % page_number)

    def get_context(self, request, items, paginator, page):
        """
        Get the context for this view.
        """
        context = super(ListView, self).get_context(request, items)
        context.update({
            'paginator': paginator,
            '%s_list' % self.template_object_name(request, items): items,
            'page_obj': page,
            'is_paginated':  paginator is not None
        })
        return context
        
    def _get_legacy_paginated_context(self, paginator, page):
        """
        Legacy template context stuff. New templates should use page_obj
        to access this instead.
        """
        return {
            'is_paginated': page_obj.has_other_pages(),
            'results_per_page': paginator.per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page': page_obj.number,
            'next': page_obj.next_page_number(),
            'previous': page_obj.previous_page_number(),
            'first_on_page': page_obj.start_index(),
            'last_on_page': page_obj.end_index(),
            'pages': paginator.num_pages,
            'hits': paginator.count,
            'page_range': paginator.page_range,        
        }
        
#
# XXX TODO HERE: convert to DetailView/ModelDetailView
#
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
        nicename = self.get_template_object_name(request, obj)
        context = template.RequestContext(request, {
            "object": obj,
            nicename: obj,
        }, self.get_context_processors(request, obj))
        
        return context

    def get_template_object_name(self, request, obj):
        """
        Get the name of the object to use in the context.
        """
        return self.template_object_name or \
               re.sub('[^a-zA-Z0-9]+', '_', obj._meta.verbose_name.lower())
                   
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
    
    def get_response(self, request, obj):
        """
        Get the response for an object; must return an HttpResponse.
        """
        template = self.get_template(request, obj)
        context = self.get_context(request, obj)
        mimetype = self.get_mimetype(request, obj)
        response = HttpResponse(template.render(context), mimetype=mimetype)
        return response

    def __call__(self, request, pk=None, slug=None, object_id=None):
        """
        The view.
        """
        pk = pk or object_id
        obj = self.get_object(request, pk, slug)
        return self.get_response(request, obj)
