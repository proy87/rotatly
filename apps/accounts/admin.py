from django.contrib import admin

from .models import Gamer


class GamerAdmin(admin.ModelAdmin):
    model = Gamer


admin.site.register(Gamer)
