"""
URL configuration for rotatly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import datetime

from django.contrib import admin
from django.urls import path
from django.urls.converters import register_converter, StringConverter

from .constants import CUSTOM_GAME_STR
from .views import track, DailyView, CustomView, CreateView, post_create


class DateConverter:
    regex = r'\d{4}-\d{2}-\d{2}'
    format = '%Y-%m-%d'

    def to_python(self, value: str) -> datetime.date:
        # Convert the URL string portion to a Python date object
        return datetime.datetime.strptime(value, self.format)

    def to_url(self, value: datetime.date) -> str:
        # Convert the Python date object back to a URL string
        return value.strftime(self.format)


class AlphaNum7Converter(StringConverter):
    regex = fr'[{CUSTOM_GAME_STR}]{{7}}'


register_converter(DateConverter, 'yyyy-mm-dd')
register_converter(AlphaNum7Converter, 'alpha_num_7')

urlpatterns = [
    path('admin-r/', admin.site.urls),
    path('', DailyView.as_view(), name='daily'),
    path('create/', CreateView.as_view(), name='create'),
    path('post-create/', post_create, name='post-create'),
    path('<yyyy-mm-dd:date>/', DailyView.as_view(), name='daily'),
    path('<alpha_num_7:slug>/', CustomView.as_view(), name='custom'),
    path('track/', track, name='track'),
]
