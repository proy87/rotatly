from django.contrib import admin

from .models import Game, Outline


class GameAdmin(admin.ModelAdmin):
    list_display = ('index',)


class OutlineAdmin(admin.ModelAdmin):
    list_display = ('index',)


admin.site.register(Game, GameAdmin)
admin.site.register(Outline, OutlineAdmin)
