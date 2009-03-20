from django.core.paginator import Paginator, InvalidPage
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.utils.encoding import smart_str
from django.views.generic2.base import GenericView

class ListView(GenericView):
    """
    Render some list of objects. This list may be any type via setting
    `self.items`, but if it's a queryset set on `self.queryset` then the
    queryset will be handled correctly.
    """
    
    def __init__(self, **kwargs):
        self._load_config_values(kwargs, 
            paginate_by = None,
            allow_empty = True,
            template_object_name = None,
            queryset = None,
            items = None,
        )
        super(ListView, self).__init__(**kwargs)
    
    def __call__(self, request, page=None):
        paginator, page, items = self.get_items(request, page)
        template = self.get_template(request, items)
        context = self.get_context(request, items, paginator, page)
        mimetype = self.get_mimetype(request, items)
        response = self.get_response(request, items, template, context, mimetype=mimetype)
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
        return self.paginate_by
        
    def get_allow_empty(self, request):
        """
        Returns ``True`` if the view should display empty lists, and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty
        
    def paginate_items(self, request, items, page):
        """
        Paginate the list of items, if needed.
        """
        paginate_by = self.get_paginate_by(request, items)
        allow_empty = self.get_allow_empty(request)
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
            
    def get_template_names(self, request, items, suffix='list'):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """ 
        names = super(ListView, self).get_template_names(request, items)
        
        # If the list is a queryset, we'll invent a template name based on the
        # app and model name. This name gets put at the end of the template 
        # name list so that user-supplied names override the automatically-
        # generated ones.
        if hasattr(items, 'model'):
            opts = items.model._meta
            names.append("%s/%s_%s.html" % (opts.app_label, opts.object_name.lower(), suffix))
        
        return names

    def get_context(self, request, items, paginator, page, context=None):
        """
        Get the context for this view.
        """
        if not context:
            context = {}
        context.update({
            'paginator': paginator,
            'object_list': items,
            'page_obj': page,
            'is_paginated':  paginator is not None
        })
        context = super(ListView, self).get_context(request, items, context)
        
        template_obj_name = self.get_template_object_name(request, items)
        if template_obj_name:
            context[template_obj_name] = items
            
        # If we're paginated, populate the context with legacy pagination
        # stuff. In 1.2 `legacy_context` will default to False, and in 1.3
        # these context variables will be removed.
        if paginator is not None and getattr(self, 'legacy_context', True):
            import warnings
            warnings.warn(
                "'%(cls)s' is using legacy context variables which will be "\
                "removed in a future version of Django. Set "\
                "'%(cls)s.legacy_content' to False to stop using these "\
                "context variables." % {'cls': self.__class__.__name__},
                PendingDeprecationWarning
            )
            context.update(self._get_legacy_paginated_context(paginator, page))
        
        return context
    
    def get_template_object_name(self, request, items):
        """
        Get the name of the item to be used in the context.
        """
        if self.template_object_name:
            return "%s_list" % self.template_object_name
        elif hasattr(items, 'model'):
            return smart_str(items.model._meta.verbose_name_plural)
        else:
            return None

    def _get_legacy_paginated_context(self, paginator, page):
        """
        Legacy template context stuff. New templates should use page_obj
        to access this instead.
        """
        return {
            'is_paginated': page.has_other_pages(),
            'results_per_page': paginator.per_page,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'page': page.number,
            'next': page.next_page_number(),
            'previous': page.previous_page_number(),
            'first_on_page': page.start_index(),
            'last_on_page': page.end_index(),
            'pages': paginator.num_pages,
            'hits': paginator.count,
            'page_range': paginator.page_range,        
        }
