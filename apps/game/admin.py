from django.contrib import admin

from .models import Daily, Custom, Outline


class GameAdmin(admin.ModelAdmin):
    list_display = ('index',)


class OutlineAdmin(admin.ModelAdmin):
    list_display = ('index',)


admin.site.register((Daily, Custom), GameAdmin)
admin.site.register(Outline, OutlineAdmin)