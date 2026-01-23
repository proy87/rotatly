import datetime
import json
import math
import re

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.game.board import init_borders, Cell
from apps.game.constants import (START_DATE, DATE_FORMAT, JS_DATE_FORMAT, CW_SYMBOLS, CCW_SYMBOLS)
from apps.game.creation import create_custom_puzzle, get_or_create_default_outline, get_or_create_daily_puzzle, normalize_create_payload
from apps.game.utils import encode, generate_target_preview
from .models import Daily, Custom
from .solver import solve, is_solved


class GameView(LoginRequiredMixin, TemplateView):
    model_class = None

    def get_game_index(self):
        raise NotImplementedError

    def get_canonical_url(self):
        raise NotImplementedError

    def get_game(self):
        """Get the game object. Can be overridden by subclasses for custom behavior."""
        return self.model_class.objects.select_related('outline').get(index=self.get_game_index())

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        moves_re = re.findall(fr'(?<!\d)([1-9]|[1-9][0-9])(?!\d)\s*([{CW_SYMBOLS}{CCW_SYMBOLS}])',
                              self.request.GET.get('moves', ''))
        pre_moves = [(int(k), v in CW_SYMBOLS) for k, v in moves_re]
        game = self.model_class.objects.select_related('outline').get(index=self.get_game_index())
        game.fixed_areas = {int(k): int(v) for k, v in game.fixed_areas.items()}
        size = int(math.sqrt(len(game.board)))
        outline = game.outline

        board = encode(game.board, game.fixed_areas_as_int)
        outline_board = encode(outline.board, game.fixed_areas_as_int, for_outline=True)

        if settings.DEBUG:
            solution = solve(board=board,
                             outline=outline_board,
                             disabled_nodes=game.disabled_nodes_as_int,
                             fixed_areas=game.fixed_areas_as_int)
            if solution:
                solution = ' '.join(f'{i}{(CW_SYMBOLS if v == 'CW' else CCW_SYMBOLS)[0]}' for i, v in solution)
            print(solution)

        # Generate target preview for showing the goal state
        target_preview_board = generate_target_preview(
            board=game.board,
            outline=outline_board,
            fixed_areas=game.fixed_areas,
        )
        # Pass target_preview_board as outline_colors so board outlines match target colors
        bordered_board = init_borders(outline=outline_board, board=board, outline_colors=target_preview_board)
        bordered_outline = init_borders(outline=outline_board, outline_colors=target_preview_board)
        target_preview = init_borders(outline=outline_board, board=target_preview_board, outline_colors=target_preview_board)
        context_data.update(dict(size=size,
                                 game=game,
                                 board=bordered_board,
                                 outline=bordered_outline,
                                 outline_dumped=json.dumps(outline_board),
                                 pre_moves=pre_moves,
                                 pre_moves_dumped=json.dumps(pre_moves),
                                 is_solved=is_solved(board, outline_board, pre_moves,
                                                     game.fixed_areas_as_int, game.disabled_nodes_as_int),
                                nodes=[[(e, game.disabled_nodes_as_int.get(e, dict())) for e in range(i, i + size - 1)]
                                       for i in
                                       range(1, (size - 1) ** 2, size - 1)],
                                target_preview=target_preview,
                                canonical_url=settings.SITE_DOMAIN + self.get_canonical_url(),
                                 moves_max_num=game.moves_min_num * 100,
                                 cw_symbol=CW_SYMBOLS[0],
                                 ccw_symbol=CCW_SYMBOLS[0]))
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

    def get_game(self):
        """Override to auto-create daily puzzle if it doesn't exist."""
        game = get_or_create_daily_puzzle(self.get_game_index())
        if game is None:
            raise Http404()
        return game

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


class CreateView(LoginRequiredMixin, TemplateView):
    template_name = 'game/create.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        outline = get_or_create_default_outline()
        size2 = len(outline.board)
        size = int(math.sqrt(size2))
        context_data.update(
            size=size,
            nodes=[[(e, dict()) for e in range(i, i + size - 1)] for i in range(1, (size - 1) ** 2, size - 1)],
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
    outline_items = [item for item in request.POST.get('outline', '').replace(' ', '').split(',') if item]
    fixed_areas_items = {}
    for item in request.POST.get('fixed_areas', '').replace(' ', '').split(','):
        if not item:
            continue
        try:
            key, value = item.split(':', 1)
        except ValueError:
            continue
        fixed_areas_items[key] = value
    board_items = [item for item in request.POST.get('board', '').replace(' ', '').split(',') if item]
    node_items = [item for item in request.POST.get('nodes', '').replace(' ', '').split(',') if item]

    outline, board, fixed_areas, nodes, error = normalize_create_payload(
        outline_items=outline_items,
        board_items=board_items,
        fixed_areas_items=fixed_areas_items,
        disabled_node_items=node_items,
    )
    if error:
        return JsonResponse({'error': error})

    game, error = create_custom_puzzle(outline, board, fixed_areas, nodes)
    if error:
        return JsonResponse({'error': error})

    return JsonResponse({'url': settings.SITE_DOMAIN + reverse('custom', args=(game.index,))})


def _get_daily_game(date: datetime.datetime | None):
    release_offset_hours = 0 if settings.DEBUG else 5
    today_date = datetime.datetime.now() - datetime.timedelta(hours=release_offset_hours)
    days_passed = (today_date - START_DATE).days
    if date is None:
        current_date = today_date
        game_index = days_passed
    else:
        current_date = date
        game_index = (current_date - START_DATE).days
        if not 0 < game_index <= days_passed:
            raise Http404()
    # Auto-create daily puzzle if it doesn't exist (handles new day start)
    game = get_or_create_daily_puzzle(game_index)
    if game is None:
        raise Http404()
    return game, current_date, today_date


@require_http_methods(["GET"])
def api_puzzle(request, date: datetime.datetime | None = None):
    try:
        game, current_date, today_date = _get_daily_game(date)
    except Http404:
        return JsonResponse({'error': 'Puzzle not found for this date.'}, status=404)
    fixed_areas = {int(k): int(v) for k, v in game.fixed_areas.items()}
    board = list(game.board)
    outline_raw = list(game.outline.board)
    outline_encoded = list(encode(outline_raw, fixed_areas, mode='outline'))
    target_preview = generate_target_preview(board, outline_encoded, fixed_areas)

    min_date = (START_DATE + datetime.timedelta(days=1)).strftime(JS_DATE_FORMAT)
    max_date = today_date.strftime(JS_DATE_FORMAT)
    date_iso = current_date.strftime(JS_DATE_FORMAT)

    return JsonResponse({
        'index': game.index,
        'board': board,
        'outline': outline_encoded,
        'targetPreview': target_preview,
        'minMoves': game.moves_min_num,
        'disabledNodes': game.disabled_nodes,
        'fixedAreas': fixed_areas,
        'date': current_date.strftime(DATE_FORMAT),
        'dateIso': date_iso,
        'minDateIso': min_date,
        'maxDateIso': max_date,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_solve(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    board = payload.get('board')
    outline = payload.get('outline')
    disabled_nodes = payload.get('disabledNodes') or {}
    fixed_areas = payload.get('fixedAreas') or {}

    if not isinstance(board, list) or not isinstance(outline, list):
        return JsonResponse({'error': 'Board and outline must be arrays.'}, status=400)
    if len(board) != len(outline):
        return JsonResponse({'error': 'Board and outline sizes do not match.'}, status=400)

    try:
        board_values = [int(v) for v in board]
        outline_values = [int(v) for v in outline]
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Board and outline must contain numbers.'}, status=400)

    try:
        fixed_areas = {int(k): int(v) for k, v in fixed_areas.items()}
    except (TypeError, ValueError, AttributeError):
        return JsonResponse({'error': 'Fixed areas are invalid.'}, status=400)

    board = tuple(board)
    try:
        game = Custom.objects.get(board=board, disabled_nodes=nodes, fixed_areas=fixed_areas, outline=outline_obj)
    except Custom.DoesNotExist:
        solution = solve(board=encode(board, fixed_areas, mode='encode'),
                         outline=encode(outline_obj.board, fixed_areas, mode='outline'),
                         disabled_nodes=nodes,
                         fixed_areas=fixed_areas)
        if solution is None:
            return JsonResponse({'error': 'The puzzle is unsolvable.'})
        n = len(solution)
        if n == 0:
            return JsonResponse({'error': 'The puzzle is already solved.'})
        game = Custom.objects.create(board=board,
                                     disabled_nodes=nodes,
                                     fixed_areas=fixed_areas,
                                     outline=outline_obj,
                                     encoded_board=encoded_board,
                                     moves_min_num=n,
                                     index=''.join(random.choices(CUSTOM_GAME_STR, k=CUSTOM_GAME_SLUG_LENGTH)))
    return JsonResponse({'url': settings.SITE_DOMAIN + reverse('custom', args=(game.index,))})
