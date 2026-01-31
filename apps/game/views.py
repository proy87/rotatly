import datetime
import json
import math
import random
import re
from collections import defaultdict

from django.conf import settings
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView

from .board import init_borders, Cell, Horizontal, Vertical, get_nodes
from .constants import (START_DATE, DATE_FORMAT, JS_DATE_FORMAT, CUSTOM_GAME_STR, CUSTOM_GAME_SLUG_LENGTH)
from .utils import encode
from .models import Daily, Custom, Outline
from .solver import solve, is_solved


class GameView(TemplateView):
    model_class = None

    def get_game_index(self):
        raise NotImplementedError

    def get_canonical_url(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        try:
            game = self.model_class.objects.select_related('outline').get(index=self.get_game_index())
        except self.model_class.DoesNotExist:
            raise Http404
        size = int(math.sqrt(len(game.board)))
        outline = game.outline

        board = encode(game.board, game.fixed_areas_as_int)
        outline_board = encode(outline.board, game.fixed_areas_as_int, for_outline=True)
        nodes = get_nodes(size, size, game.disabled_nodes_as_dict)
        symbols = set()
        for node in nodes:
            symbols.update([node.symbol, node.reverse_symbol])
        moves_re = re.findall(fr'[1-9]\s*[{symbols}]', self.request.GET.get('moves', ''))
        pre_moves = [(int(k), v) for k, v in moves_re]
        if settings.DEBUG:
            solution = solve(board=board,
                             outline=outline_board,
                             nodes=nodes,
                             fixed_areas=game.fixed_areas_as_int)
            if solution:
                solution = ' '.join(f'{i}{v}' for i, v in solution)
            print(solution)

        vals = list(game.fixed_areas_as_int.values())
        bordered_board = init_borders(outline=outline_board, board=[-ch if ch in vals else ch for ch in game.board])
        bordered_outline = init_borders(outline=outline_board)
        context_data.update(dict(size=size,
                                 game=game,
                                 board=bordered_board,
                                 outline=bordered_outline,
                                 outline_dumped=json.dumps(outline_board),
                                 pre_moves=pre_moves,
                                 pre_moves_dumped=json.dumps(pre_moves),
                                 is_solved=is_solved(board, outline_board, pre_moves,
                                                     game.fixed_areas_as_int, game.disabled_nodes_as_dict),
                                 nodes=nodes,
                                 canonical_url=settings.SITE_DOMAIN + self.get_canonical_url(),
                                 moves_max_num=game.moves_min_num * 100))
        return context_data


class CustomView(GameView):
    template_name = 'game/custom.html'
    model_class = Custom

    def get_game_index(self):
        return self.kwargs['slug']

    def get_canonical_url(self):
        return reverse('custom', args=(self.kwargs['slug'],))


class DailyMixin:
    viewname = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.today_date = None
        self.game_index = None
        self.current_date = None

    def setup(self, request, *args, date=None, **kwargs):
        super().setup(request, *args, **kwargs)
        self.today_date = datetime.datetime.now() - datetime.timedelta(hours=7 if settings.DEBUG else 5)
        days_passed = (self.today_date - START_DATE).days
        if date is not None:
            self.game_index = (date - START_DATE).days
            if not 0 < self.game_index <= days_passed:
                raise Http404()
            self.current_date = date
        else:
            self.game_index = days_passed
            self.current_date = self.today_date

    def get_context_data(self, date=None, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(dict(current_date=self.current_date.strftime(DATE_FORMAT),
                                 min_date_js=(START_DATE + datetime.timedelta(days=1)).strftime(JS_DATE_FORMAT),
                                 max_date_js=self.today_date.strftime(JS_DATE_FORMAT),
                                 current_date_js=self.current_date.strftime(JS_DATE_FORMAT), ))
        return context_data


class DailyView(DailyMixin, GameView):
    template_name = 'game/daily.html'
    model_class = Daily

    def get_game_index(self):
        return self.game_index

    def get_canonical_url(self):
        return reverse('daily', args=(self.current_date,))

    def get_context_data(self, date=None, **kwargs):
        context_data = super().get_context_data(**kwargs)
        game_index = self.get_game_index()
        if date is None:
            next_puzzle_url = None
        else:
            kwargs = dict()
            days_to_today = (self.today_date - date).days
            if days_to_today > 1:
                kwargs['date'] = self.current_date + datetime.timedelta(days=1)
            next_puzzle_url = None if days_to_today < 1 else reverse('daily', kwargs=kwargs)
        context_data.update(dict(archived=date is not None,
                                 previous_puzzle_url=None if game_index == 1 else reverse('daily', kwargs={
                                     'date': self.current_date - datetime.timedelta(days=1)}),
                                 next_puzzle_url=next_puzzle_url, ))
        return context_data


class CreateView(TemplateView):
    template_name = 'game/create.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        outlines = Outline.objects.all()
        size2 = len(outlines[0].board)
        size = int(math.sqrt(size2))
        context_data.update(
            size=size,
            nodes=get_nodes(size, size),
            empty_outline=init_borders([0] * size2),
            empty_board=init_borders([0] * size2, [0] * size2),
            names=[(i, Cell.names_dict[i], c) for i, c in Cell.colors_dict.items()],
            tetraminoes=[dict(name='I',
                              cells=[Cell(0, 0, True, dict(left=True, top=True, bottom=True)),
                                     Cell(0, 1, True, dict(top=True, bottom=True)),
                                     Cell(0, 2, True, dict(top=True, bottom=True)),
                                     Cell(0, 3, True, dict(right=True, top=True, bottom=True))]),
                         dict(name='T',
                              cells=[Cell(0, 0, True, dict(left=True, top=True, bottom=True)),
                                     Cell(0, 1, True, dict(top=True)),
                                     Cell(0, 2, True, dict(top=True, bottom=True, right=True)),
                                     Cell(1, 1, True, dict(right=True, left=True, bottom=True))]),
                         dict(name='L',
                              cells=[Cell(0, 0, True, dict(left=True, top=True)),
                                     Cell(0, 1, True, dict(top=True, bottom=True)),
                                     Cell(0, 2, True, dict(top=True, bottom=True, right=True)),
                                     Cell(1, 0, True, dict(right=True, left=True, bottom=True))]),
                         dict(name='J',
                              cells=[Cell(0, 0, True, dict(left=True, top=True, bottom=True)),
                                     Cell(0, 1, True, dict(top=True, bottom=True)),
                                     Cell(0, 2, True, dict(top=True, right=True)),
                                     Cell(1, 2, True, dict(right=True, left=True, bottom=True))]),
                         dict(name='S',
                              cells=[Cell(0, 1, True, dict(left=True, top=True)),
                                     Cell(0, 2, True, dict(top=True, right=True, bottom=True)),
                                     Cell(1, 0, True, dict(top=True, bottom=True, left=True)),
                                     Cell(1, 1, True, dict(right=True, bottom=True))]),
                         dict(name='Z',
                              cells=[Cell(0, 0, True, dict(left=True, top=True, bottom=True)),
                                     Cell(0, 1, True, dict(top=True, right=True)),
                                     Cell(1, 1, True, dict(bottom=True, left=True)),
                                     Cell(1, 2, True, dict(right=True, bottom=True, top=True))]),
                         dict(name='O',
                              cells=[Cell(0, 0, True, dict(left=True, top=True)),
                                     Cell(0, 1, True, dict(top=True, right=True)),
                                     Cell(1, 0, True, dict(bottom=True, left=True)),
                                     Cell(1, 1, True, dict(right=True, bottom=True))]),
                         ]
        )
        return context_data


def track(request):
    if not settings.DEBUG:
        from django.core.mail import send_mail
        send_mail('Rotatly',
                  request.POST,
                  None,
                  [a[1] for a in settings.ADMINS])
    return JsonResponse({})


def post_create(request):
    if False and not request.user.is_authenticated:
        return JsonResponse({'error': 'You should be logged in.'})

    elements = (1, 2, 3, 4)

    outline = []
    mapping = {}
    next_id = 0
    for item in request.POST.get('outline', '').replace(' ', '').split(','):
        if item not in mapping:
            mapping[item] = next_id
            next_id += 1
        outline.append(mapping[item])

    if len(outline) != 16:
        return JsonResponse({'error': 'Incomplete outline.'})

    if len(mapping) != 4:
        return JsonResponse({'error': 'Invalid outline.'})

    fixed_areas = {}
    for item in request.POST.get('fixed_areas', '').replace(' ', '').split(','):
        try:
            key, value = item.split(':')
        except:
            continue
        else:
            if key in mapping:
                try:
                    value = int(value)
                    if not 1 <= value <= 4:
                        raise Exception
                except:
                    continue
                else:
                    fixed_areas[mapping[key] + 1] = value
    vals = list(fixed_areas.values())
    vals_n = len(vals)
    if vals_n != len(set(vals)):
        return JsonResponse({'error': 'Invalid outline.'})
    if vals_n == 3:
        els = set(elements)
        k = els.difference(fixed_areas.keys()).pop()
        v = els.difference(vals).pop()
        fixed_areas[k] = v
    fixed_areas = {k: v for k, v in sorted(fixed_areas.items())}

    board = []
    for item in request.POST.get('board', '').replace(' ', '').split(','):
        try:
            n = int(item)
            if not 1 <= n <= 4:
                raise Exception
            board.append(n)
        except:
            pass

    if len(board) != 16:
        return JsonResponse({'error': 'Incomplete board.'})

    if any(len([c for c in board if c == e]) != 4 for e in elements):
        return JsonResponse({'error': 'Invalid board.'})

    nodes = defaultdict(dict)
    for item in request.POST.get('nodes', '').replace(' ', '').split(','):
        if len(item) == 1:
            try:
                n = int(item)
                if not 1 <= n <= 9:
                    raise Exception
                nodes[n] = {"direct": True, "reverse": True}
            except:
                pass
        elif len(item) == 2:
            digit, direction = item
            try:
                n = int(digit)
                if not 1 <= n <= 4:
                    raise Exception
            except:
                pass
            else:
                if direction == Vertical.symbol:
                    nodes[n + 9]['direct'] = True
                elif direction == Vertical.reverse_symbol:
                    nodes[n + 9]['reverse'] = True
                elif direction == Horizontal.symbol:
                    nodes[n + 9 + 4]['direct'] = True
                elif direction == Horizontal.reverse_symbol:
                    nodes[n + 9 + 4]['reverse'] = True

    nodes = [(k, v.get('direct', False), v.get('reverse', False)) for k, v in sorted(nodes.items(), key=lambda o: o[0])]
    inactive = 0
    for a, b, c in nodes:
        if b:
            inactive += 1
        if c:
            inactive += 1
    if inactive == 9 + 4 + 4:
        return JsonResponse({'error': 'No active nodes.'})

    m = {}
    next_id = 0
    encoded_board = []
    for item in board:
        if not item in m:
            m[item] = next_id
            next_id += 1
        encoded_board.append(m[item])

    outline = tuple(outline)
    try:
        outline_obj = Outline.objects.get(board=outline)
    except Outline.DoesNotExist:
        return JsonResponse({'error': 'Invalid outline.'})

    board = tuple(board)
    try:
        game = Custom.objects.get(board=board, disabled_nodes=nodes, fixed_areas=fixed_areas, outline=outline_obj)
    except Custom.DoesNotExist:
        game = Custom(board=board,
                      disabled_nodes=nodes,
                      fixed_areas=fixed_areas,
                      outline=outline_obj,
                      encoded_board=encoded_board,
                      index=''.join(random.choices(CUSTOM_GAME_STR, k=CUSTOM_GAME_SLUG_LENGTH)))
        solution = solve(board=encode(board, fixed_areas),
                         outline=encode(outline_obj.board, fixed_areas, for_outline=True),
                         nodes=get_nodes(4, 4, game.disabled_nodes_as_dict),
                         fixed_areas=fixed_areas)
        if solution is None:
            return JsonResponse({'error': 'The puzzle is unsolvable.'})
        n = len(solution)
        if n == 0:
            return JsonResponse({'error': 'The puzzle is already solved.'})
        game.moves_min_num = n
        game.save()
    return JsonResponse({'url': settings.SITE_DOMAIN + reverse('custom', args=(game.index,))})
