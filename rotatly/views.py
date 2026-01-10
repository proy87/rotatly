import datetime
import json
import math
import re

from django.conf import settings
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView

from .board import init_borders
from .constants import START_DATE, DATE_FORMAT, JS_DATE_FORMAT, CW_SYMBOLS, CCW_SYMBOLS
from .models import Daily, Custom, Outline
from .solver import solve, is_solved
from .utils import encode


class GameView(TemplateView):
    model_class = None

    def get_game_index(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        moves_re = re.findall(fr'(?<!\d)([1-9]|[1-9][0-9])(?!\d)\s*([{CW_SYMBOLS}{CCW_SYMBOLS}])',
                              self.request.GET.get('moves', ''))
        pre_moves = [(int(k), v in CW_SYMBOLS) for k, v in moves_re]
        game = self.model_class.objects.select_related('outline').get(index=self.get_game_index())
        game.fixed_areas = {int(k): int(v) for k, v in game.fixed_areas.items()}
        size = int(math.sqrt(len(game.board)))
        outline = game.outline
        board = encode(game.board, game.fixed_areas, mode='encode')
        outline_board = encode(outline.board, game.fixed_areas, mode='outline')

        if settings.DEBUG:
            solution = solve(board=encode(game.board, game.fixed_areas),
                             outline=outline_board,
                             disabled_nodes=game.disabled_nodes,
                             fixed_areas=game.fixed_areas)
            print(solution)

        bordered_board = init_borders(outline=outline_board, board=board)
        bordered_outline = init_borders(outline=outline_board)
        context_data.update(dict(size=size,
                                 game=game,
                                 board=bordered_board,
                                 outline=bordered_outline,
                                 outline_dumped=json.dumps(outline_board),
                                 pre_moves=pre_moves,
                                 pre_moves_dumped=json.dumps(pre_moves),
                                 is_solved=is_solved(board, outline_board, pre_moves, game.fixed_areas,
                                                     game.disabled_nodes),
                                 nodes=[[(e, game.disabled_nodes.get(str(e), dict())) for e in range(i, i + size - 1)]
                                        for i in
                                        range(1, (size - 1) ** 2, size - 1)],
                                 moves_max_num=game.moves_min_num * 100,
                                 cw_symbol=CW_SYMBOLS[0],
                                 ccw_symbol=CCW_SYMBOLS[0],
                                 debug=settings.DEBUG))
        return context_data


class CustomView(GameView):
    template_name = 'game/custom.html'
    model_class = Custom

    def get_game_index(self):
        return self.kwargs['slug']


class DailyView(GameView):
    template_name = 'game/daily.html'
    model_class = Daily

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.today_date = None
        self.game_index = None
        self.current_date = None

    def setup(self, request, *args, date=None, **kwargs):
        super().setup(request, *args, **kwargs)
        self.today_date = datetime.datetime.now() - datetime.timedelta(hours=7 if settings.DEBUG else -1)
        days_passed = (self.today_date - START_DATE).days
        if date is not None:
            self.game_index = (date - START_DATE).days
            if not 0 < self.game_index <= days_passed:
                raise Http404()
            self.current_date = date
        else:
            self.game_index = days_passed
            self.current_date = self.today_date

    def get_game_index(self):
        return self.game_index

    def get_context_data(self, date=None, **kwargs):
        context_data = super().get_context_data(**kwargs)
        game_index = context_data['game'].index
        if date is None:
            next_puzzle_url = None
        else:
            kwargs = dict()
            days_to_today = (self.today_date - date).days
            if days_to_today > 1:
                kwargs['date'] = self.current_date + datetime.timedelta(days=1)
            next_puzzle_url = None if days_to_today < 1 else reverse('daily', kwargs=kwargs)
        context_data.update(dict(archived=date is not None,
                                 current_date=self.current_date.strftime(DATE_FORMAT),
                                 canonical_url=reverse('daily', args=(self.current_date,)),
                                 previous_puzzle_url=None if game_index == 1 else reverse('daily', kwargs={
                                     'date': self.current_date - datetime.timedelta(days=1)}),
                                 next_puzzle_url=next_puzzle_url,
                                 min_date_js=(START_DATE + datetime.timedelta(days=1)).strftime(JS_DATE_FORMAT),
                                 max_date_js=self.today_date.strftime(JS_DATE_FORMAT),
                                 current_date_js=self.current_date.strftime(JS_DATE_FORMAT), ))
        return context_data


class CreateView(TemplateView):
    template_name = 'game/create.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        outlines = Outline.objects.all()
        context_data['outlines'] = [(outline.index, init_borders(outline.board)) for outline in outlines]
        context_data['size'] = int(math.sqrt(len(outlines[0].board)))
        return context_data


def track(request):
    if not settings.DEBUG:
        from django.core.mail import send_mail
        send_mail('Rotatly',
                  str(request.GET),
                  None,
                  [a[1] for a in settings.ADMINS])
    return JsonResponse({})
