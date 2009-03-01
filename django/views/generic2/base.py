from django.core.exceptions import ImproperlyConfigured
    
class GenericView(object):
    """
    Parent class for all generic views. Handles the wrapping of options defined
    as attributes, and also defines the options and defaults shared by all
    generic views.
    """
        
    def __init__(self, **kwargs):
        self.context_processors = kwargs.pop('context_processors', None)
        self.mimetype = kwargs.pop('mimetype', 'text/html')
        self.template_loader = kwargs.pop('template_loader', None)
        self.template_name = kwargs.pop('template_name', None)
        if kwargs:
            badkey = kwargs.iterkeys.next()
            raise TypeError("__init__() got an unexpected keyword argument '%s'" % badkey)
    
    def get_context_processors(self, request, obj):
        """
        Get the context processors to be used for the given request.
        """
        return self.context_processors or None
    
    def get_mimetype(self, request, obj):
        """
        Get the mimetype to be used for the given request.
        """
        return self.mimetype or "text/html"
                                
    def get_template(self, request, obj):
        """
        Get a ``Template`` object for the given request.
        """
        names = self.get_template_names(request, obj)
        if not names:
            raise ImproperlyConfigured("'%s' must provide template_name." % self.__class__.__name__)
        return self.load_template(request, obj, names)

    def get_template_loader(self, request, obj):
        """
        Get the template loader to be used for this request. Defaults to 
        ``django.template.loader``.
        """
        import django.template.loader
        return self.template_loader or django.template.loader

    def get_template_name(self, request, obj):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """ 
        if self.template_name is None:
            return []                       
        elif isinstance(self.template_name, basestring):
            return [self.template_name]
        else:
            
    def load_template(self, request, obj, names=[]):
        """
        Load a template, using self.template_loader or the default.
        """
        return self.get_template_loader(request, obj).select_template(names)
        
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
    
    paginate_by          = None
    allow_empty          = True
    template_object_name = None
    
    def __call__(self, request, page=None):
        paginator, page, items = self.get_items(request, page)
        template = self.get_template(request, items)
        context = self.get_context(request, items, paginator, page)
        mimetype = self.get_mimetype(request, items)
        response = HttpResponse(template.render(context), mimetype=mimetype)
        response = self.process_response(response)
        return response

    def get_items(self, request, page):
        """
        Get the list of items for this view. This must be an interable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        if hasattr(self, 'queryset') and self.queryset is not None:
            items = self.queryset._clone()
        elif hasattr(self, 'items') and self.items is not None:
            items = self.items
        else:
            raise ImproperlyConfigured("'%s' must define 'queryset' or 'items'" \
                                            % self.__class__.__name__)
        
        return self.paginate_items(request, items, page)

    def get_paginate_by(self, request, items):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        return self.paginate_by or None
        
    def get_allow_empty(self, request, items):
        """
        Returns ``True`` if the view should display empty lists, and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty or True
        
    def paginate_items(self, request, items, page):
        """
        Paginate the list of items, if needed.
        """
        paginate_by = self.get_paginate_by(request, items)
        allow_empty = self.get_allow_empty(request, items)
        if not paginate_by:
            if not allow_empty and len(items) == 0:
                raise Http404("Empty list and '%s.allow_empty' is False." % self.__class__.__name__)
            return (None, None, items)
        
        paginator = Paginator(items, paginate_by, allow_empty_first_page=allow_empty)
        page = page or request.GET.get('page', 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404("Page is not 'last', nor can it be converted to an int.")
        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list)
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
        if getattr(self, 'legacy_context', True):
            context.update(self._get_legacy_paginated_context(paginator, page))
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
