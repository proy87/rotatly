import datetime

from django.urls import path
from django.urls.converters import register_converter, StringConverter

from .constants import CUSTOM_GAME_STR, CUSTOM_GAME_SLUG_LENGTH
from .views import track, DailyView, CustomView, CreateView, post_create, api_puzzle, api_solve


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
    regex = fr'[{CUSTOM_GAME_STR}]{{{CUSTOM_GAME_SLUG_LENGTH}}}'


register_converter(DateConverter, 'yyyy-mm-dd')
register_converter(AlphaNum7Converter, 'alpha_num_7')

urlpatterns = [
    path('api/puzzle/', api_puzzle, name='api-puzzle'),
    path('api/puzzle/<yyyy-mm-dd:date>/', api_puzzle, name='api-puzzle-date'),
    path('api/solve/', api_solve, name='api-solve'),
    path('', DailyView.as_view(), name='daily'),
    path('create/', CreateView.as_view(), name='create'),
    path('post-create/', post_create, name='post-create'),
    path('<yyyy-mm-dd:date>/', DailyView.as_view(), name='daily'),
    path('<alpha_num_7:slug>/', CustomView.as_view(), name='custom'),
    path('track/', track, name='track'),
]
