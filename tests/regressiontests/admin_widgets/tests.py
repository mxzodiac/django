from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from unittest import TestCase
import models

class AdminFormfieldForDBFieldTests(TestCase):
    """
    Tests for correct behavior of ModelAdmin.formfield_for_dbfield
    """

    def assertFormfield(self, model, fieldname, widgetclass=None, **admin_overrides):
        """
        Helper to call formfield_for_dbfield for a given model and field name
        and verify that the returned formfield is appropriate.
        """
        ma = admin.ModelAdmin(model, admin.site)
        for k in admin_overrides:
            setattr(ma, k, admin_overrides[k])
            
        ff = ma.formfield_for_dbfield(model._meta.get_field(fieldname))
        if widgetclass:
            # "unwrap" the widget wrapper, if needed
            if isinstance(ff.widget, widgets.RelatedFieldWidgetWrapper):
                widget = ff.widget.widget
            else:
                widget = ff.widget
                
            self.assert_(
                isinstance(widget, widgetclass), 
                "Wrong widget for %s.%s: expected %s, got %s" % \
                    (model.__class__.__name__, fieldname, widgetclass, type(widget))
            )
            
        # Return the formfield so that other tests can continue
        return ff
    
    def testDateField(self):
        self.assertFormfield(models.Event, 'date', widgets.AdminDateWidget)
        
    def testDateTimeField(self):
        self.assertFormfield(models.Member, 'birthdate', widgets.AdminSplitDateTime)
        
    def testTimeField(self):
        self.assertFormfield(models.Event, 'start_time', widgets.AdminTimeWidget)

    def testTextField(self):
        self.assertFormfield(models.Event, 'description', widgets.AdminTextareaWidget)
    
    def testURLField(self):
        self.assertFormfield(models.Event, 'link', widgets.AdminURLFieldWidget)

    def testIntegerField(self):
        self.assertFormfield(models.Event, 'min_age', widgets.AdminIntegerFieldWidget)
        
    def testCharField(self):
        self.assertFormfield(models.Member, 'name', widgets.AdminTextInputWidget)
        
    def testFileField(self):
        self.assertFormfield(models.Album, 'cover_art', widgets.AdminFileWidget)
        
    def testForeignKey(self):
        self.assertFormfield(models.Event, 'band', forms.Select)
        
    def testRawIDForeignKey(self):
        self.assertFormfield(models.Event, 'band', widgets.ForeignKeyRawIdWidget,
                             raw_id_fields=['band'])
    
    def testRadioFieldsForeighKey(self):
        ff = self.assertFormfield(models.Event, 'band', widgets.AdminRadioSelect, 
                                  radio_fields={'band':admin.VERTICAL})
        self.assertEqual(ff.empty_label, None)
        
    def testManyToMany(self):
        self.assertFormfield(models.Band, 'members', forms.SelectMultiple)
    
    def testRawIDManyTOMany(self):
        self.assertFormfield(models.Band, 'members', widgets.ManyToManyRawIdWidget,
                             raw_id_fields=['members'])
    
    def testFilteredManyToMany(self):
        self.assertFormfield(models.Band, 'members', widgets.FilteredSelectMultiple,
                             filter_vertical=['members'])
