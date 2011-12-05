from django.contrib import admin

from models import Original, Converted


class ConvertedAdmin(admin.ModelAdmin):
    pass

admin.site.register(Original)
admin.site.register(Converted, ConvertedAdmin)