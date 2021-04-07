from django.contrib import admin

from .models import Category

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'slug']
    prepopulated_fields = {'slug': ('category_name',)}

admin.site.register(Category, CategoryAdmin)