"""
A second, custom AdminSite -- see tests.CustomAdminSiteTests.
"""
from django.contrib import admin
import models

class Admin2(admin.AdminSite):
    login_template = 'custom_admin/login.html'
    index_template = 'custom_admin/index.html'
    
    # A custom index view.
    def index(self, request, extra_context=None):
        return super(Admin2, self).index(request, {'foo': '*bar*'})
    
site = Admin2(name="admin2")

site.register(models.Article, models.ArticleAdmin)
site.register(models.Section, inlines=[models.ArticleInline])
site.register(models.Thing, models.ThingAdmin)