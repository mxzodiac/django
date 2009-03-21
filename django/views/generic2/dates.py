import time
import datetime
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.views.generic2 import ListView

class DateView(ListView):
    """
    Abstract base class for date-based views.
    """
    def __init__(self, **kwargs):
        self._load_config_values(kwargs, 
            allow_future = False,
            date_field = None,
        )
        super(DateView, self).__init__(**kwargs)
        
        # Never use legacy pagination context since previous date-based
        # views weren't paginated.
        self.legacy_context = False
        
    def __call__(self, request, *args, **kwargs):
        date_list, items, extra_context = self.get_dated_items(request, *args, **kwargs)
        template = self.get_template(request, items)
        context = self.get_context(request, items, date_list, extra_context)
        mimetype = self.get_mimetype(request, items)
        response = self.get_response(request, items, template, context, mimetype=mimetype)
        return response

    def get_queryset(self, request):
        """
        Get the queryset to look an objects up against. May not be called if
        `get_dated_items` is overridden.
        """
        if self.queryset is None:
            raise ImproperlyConfigured("%(cls)s is missing a queryset. Define "\
                                       "%(cls)s.queryset, or override "\
                                       "%(cls)s.get_dated_items()." \
                                       % {'cls': self.__class__.__name__})
        return self.queryset._clone()
    
    def get_dated_queryset(self, request, allow_future=False, **lookup):
        """
        Get a queryset properly filtered according to `allow_future` and any
        extra lookup kwargs.
        """
        qs = self.get_queryset(request).filter(**lookup)
        date_field = self.get_date_field(request)
        allow_future = allow_future or self.get_allow_future(request)
        allow_empty = self.get_allow_empty(request)
    
        if not allow_future:
            qs = qs.filter(**{'%s__lte' % date_field: datetime.datetime.now()})
        
        if not allow_empty and not qs:
            raise Http404("No %s available" % qs.model._meta.verbose_name_plural)
        
        return qs
        
    def get_date_list(self, request, queryset, date_type):
        """
        Get a date list by calling `queryset.dates()`, checking along the way
        for empty lists that aren't allowed.
        """
        date_field = self.get_date_field(request)
        allow_empty = self.get_allow_empty(request)

        date_list = queryset.dates(date_field, date_type)[::-1]
        if date_list is not None and not date_list and not allow_empty:
            raise Http404("No %s available" % queryset.model._meta.verbose_name_plural)
            
        return date_list
            
    def get_date_field(self, request):
        """
        Get the name of the date field to be used to filter by.
        """
        return self.date_field
    
    def get_allow_future(self, request):
        """
        Returns `True` if the view should be allowed to display objects from 
        the future.
        """
        return self.allow_future
        
    def get_context(self, request, items, date_list, context=None):
        """
        Get the context. Must return a Context (or subclass) instance.
        """
        if not context:
            context = {}
        context['date_list'] = date_list
        return super(DateView, self).get_context(
            request, items, paginator=None, page=None, context=context,
        )
        
    def get_template_names(self, request, items):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """        
        return super(DateView, self).get_template_names(request, items, suffix=self._template_name_suffix)        
        
    def get_dated_items(self, request, *args, **kwargs):
        """
        Return (date_list, items, extra_context) for this request.
        """
        raise NotImplementedError()
    
class ArchiveView(DateView):
    """
    Top-level archive of date-based items.
    """
    
    _template_name_suffix = 'archive'
    
    def __init__(self, **kwargs):
        self._load_config_values(kwargs, num_latest=15)
        super(ArchiveView, self).__init__(**kwargs)
        
    def get_dated_items(self, request):
        """
        Return (date_list, items, extra_context) for this request.
        """
        qs = self.get_dated_queryset(request)
        date_list = self.get_date_list(request, qs, 'year')
        num_latest = self.get_num_latest(request)
        
        if date_list and num_latest:
            latest = qs.order_by('-'+self.get_date_field(request))[:num_latest]
        else:
            latest = None
        
        return (date_list, latest, {})
                
    def get_num_latest(self, request):
        """
        Get the number of latest items to show on the archive page.
        """
        return self.num_latest
                    
    def get_template_object_name(self, request, items):
        """
        Get the name of the item to be used in the context.
        """
        return self.template_object_name or 'latest'
        
class YearView(DateView):
    """
    List of objects published in a given year.
    """
    
    _template_name_suffix = 'archive_year'
    
    def __init__(self, **kwargs):
        # Override the allow_empty default from ListView
        allow_empty = kwargs.pop('allow_empty', getattr(self, 'allow_empty', False))
        self._load_config_values(kwargs, make_object_list=False)
        super(YearView, self).__init__(allow_empty=allow_empty, **kwargs)
    
    def get_dated_items(self, request, year):
        """
        Return (date_list, items, extra_context) for this request.
        """
        # Yes, no error checking: the URLpattern ought to validate this; it's
        # an error if it doesn't.
        year = int(year)
        date_field = self.get_date_field(request)
        qs = self.get_dated_queryset(request, **{date_field+'__year': year})
        date_list = self.get_date_list(request, qs, 'month')
        
        if self.get_make_object_list(request):
            object_list = qs.order_by('-'+date_field)
        else:
            # We need this to be a queryset since parent classes introspect it
            # to find information about the model.
            object_list = qs.none()
            
        return (date_list, object_list, {'year': year})
            
    def get_make_object_list(self, request):
        """
        Return `True` if this view should contain the full list of objects in
        the given year.
        """
        return self.make_object_list
        
class MonthView(DateView):
    """
    List of objects published in a given year.
    """
    
    _template_name_suffix = 'archive_month'
    
    def __init__(self, **kwargs):
        # Override the allow_empty default from ListView
        allow_empty = kwargs.pop('allow_empty', getattr(self, 'allow_empty', False))
        self._load_config_values(kwargs, month_format='%b')
        super(MonthView, self).__init__(allow_empty=allow_empty, **kwargs)
        
    def get_dated_items(self, request, year, month):
        """
        Return (date_list, items, extra_context) for this request.
        """
        date_field = self.get_date_field(request)
        date = _date_from_string(year, '%Y', month, self.get_month_format(request))
        
        # Construct a date-range lookup.
        first_day, last_day = _month_bounds(date)        
        lookup_kwargs = {
            '%s__gte' % date_field: first_day,
            '%s__lt' % date_field: last_day,
        }

        allow_future = self.get_allow_future(request)
        qs = self.get_dated_queryset(request, allow_future=allow_future, **lookup_kwargs)
        date_list = self.get_date_list(request, qs, 'day')
        
        # Construct a set of callbacks for getting the next and previous 
        # months. This can be expensive -- see get_next/previous_month for
        # details -- so we need to memoize them. We'll do this by creating
        # a couple of closures over a cache dict; remember that storing state
        # on self is right out.
        memo = {}
        def get_next_month():
            if 'next' not in memo:
                memo['next'] = self.get_next_month(request, date)
            return memo['next']
            
        def get_previous_month():
            if 'prev' not in memo:
                memo['prev'] = self.get_previous_month(request, date)
            return memo['prev']
        
        return (date_list, qs, {
            'month': date,
            'next_month': get_next_month,
            'previous_month': get_previous_month,
        })

    def get_next_month(self, request, date):
        """
        Get the next valid month.
        
        This is a bit complicated:
        
            * If allow_empty and allow_future are both true, this is easy:
              just return the next month.
              
            * If allow_empty is true and the next month isn't in the future,
              then return the next month.
              
            * If allow_empty is true and the next month *is* in the future,
              then return None.
              
            * If allow_empty is false and allow_future is true, return the
              next month *that contains a valid object*, even if it's in the 
              future. If there are no next objects, return None.
              
            * If allow_empty is false and allow_future is false, return the
              next month that contains a valid object. If that month is in
              the future, or if there are no next objects, return None.
              
        """
        first_day, last_day = _month_bounds(date)
        date_field = self.get_date_field(request)
        allow_empty = self.get_allow_empty(request)
        allow_future = self.get_allow_future(request)
        
        # Naively get the next month. This only works if allow_empty is True,
        # but it's cheap.
        next = (last_day + datetime.timedelta(days=1)).replace(day=1)
                    
        # Only perform a database hit if we need to find a month that actually
        # has data in it. We'll do that by looking up an object with a date at
        # least in the next month.
        if not allow_empty:
            qs = self.get_queryset(request)\
                     .filter(**{'%s__gte' % date_field: next})\
                     .order_by(date_field)
            try:
                obj = qs[0]
            except IndexError:
                next = None
            else:
                next = getattr(obj, date_field).replace(day=1)
        
        return _check_date(next, allow_future)
            
    def get_previous_month(self, request, date):
        """
        Get the previous valid month.
        
        The logic below works similarly to the login in get_next_month; see
        that docstring for why this is so complicated.
        """
        first_day, last_day = _month_bounds(date)
        date_field = self.get_date_field(request)
        allow_empty = self.get_allow_empty(request)
        allow_future = self.get_allow_future(request)
        
        # Naively get the previous month. This only works if allow_empty is
        # True but it's cheap.
        prev = (first_day - datetime.timedelta(days=1)).replace(day=1)
        
        # Only perform a database hit if we need to find a month that actually
        # has data in it. We'll do that by looking up an object with a date at
        # least in the previous month.
        if not allow_empty:
            qs = self.get_queryset(request)\
                     .filter(**{'%s__lte' % date_field: prev})\
                     .order_by('-%s' % date_field)
            try:
                obj = qs[0]
            except IndexError:
                prev = None
            else:
                prev = getattr(obj, date_field).replace(day=1)
            
        return _check_date(prev, allow_future)

    def get_month_format(self, request):
        """
        Get a month format string in strptime syntax to be used to parse the
        month from url variables.
        """
        return self.month_format

class WeekView(DateView):
    """
    List of objects published in a given week.
    """
    
    _template_name_suffix = 'archive_year'
    
    def __init__(self, **kwargs):
        # Override the allow_empty default from ListView
        allow_empty = kwargs.pop('allow_empty', getattr(self, 'allow_empty', False))
        super(WeekView, self).__init__(allow_empty=allow_empty, **kwargs)
    
    def get_dated_items(self, request, year, week):
        """
        Return (date_list, items, extra_context) for this request.
        """
        date_field = self.get_date_field(request)
        date = _date_from_string(year, '%Y', '0', '%w', week, '%U')
        
        # Construct a date-range lookup.
        first_day = date
        last_day = date + datetime.timedelta(days=7)
        lookup_kwargs = {
            '%s__gte' % date_field: first_day,
            '%s__lt' % date_field: last_day,
        }
        
        allow_future = self.get_allow_future(request)
        qs = self.get_dated_queryset(request, allow_future=allow_future, **lookup_kwargs)
        
        return (None, qs, {'week': date})
        
def _date_from_string(year, year_format, month, month_format, day='', day_format='', delim='__'):
    """
    Helper: get a datetime.date object given a format string and a year,
    month, and possibly day; raise a 404 for an invalid date.
    """
    format = delim.join((year_format, month_format, day_format))
    datestr = delim.join((year, month, day))
    try:
        return datetime.date(*time.strptime(datestr, format)[:3])
    except ValueError:
        raise Http404("Invalid date string '%s' given format '%s'" % (datestr, format))
                      
def _month_bounds(date):
    """
    Helper: return the first and last days of the month for the given date.
    """
    first_day = date.replace(day=1)
    if first_day.month == 12:
        last_day = first_day.replace(year=first_day.year + 1, month=1)
    else:
        last_day = first_day.replace(month=first_day.month + 1)
    
    return first_day, last_day

def _check_date(date, allow_future):
    """
    Helper: return None if allow_future is False and the date is in the
    future; otherwise return the date.
    """
    # Convert a datetime to a date
    if hasattr(date, 'date'):
        date = date.date()
        
    # Check against future dates.
    if date and (allow_future or date < datetime.date.today()):
        return date
    else:
        return None