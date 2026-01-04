import math
import re
import json
import datetime

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from .board import init_borders
from .solver import solve, is_solved
from .models import Game

CW_SYMBOLS = '↻L←'
CCW_SYMBOLS = '↺R→'


def rotatly(request, date=None):
    start_date = datetime.datetime(2025, 11, 25)
    today_date = datetime.datetime.now() - datetime.timedelta(hours=7 if settings.DEBUG else -1)
    days_passed = (today_date - start_date).days
    if date is not None:
        game_index = (date - start_date).days
        if not 0 < game_index <= days_passed:
            raise Http404()
        current_date = date
    else:
        game_index = days_passed
        current_date = today_date

    moves_re = re.findall(fr'(?<!\d)([1-9]|[1-9][0-9])(?!\d)\s*([{CW_SYMBOLS}{CCW_SYMBOLS}])', request.GET.get('moves', ''))
    pre_moves = [(int(k), v in CW_SYMBOLS) for k, v in moves_re]
    from .models import Outline
    from .utils import generate_random_square, encode
    board = [3, 1, 3, 2, 5, 2, 1, 4, 5, 5, 4, 3, 1, 1, 5, 4, 3, 5, 2, 4, 3, 2, 2, 4, 1]
    game = Game(index=40, board=board, encoded_board=encode(board), moves_min_num=5,
                disabled_nodes={k: dict() for k in range(1, 17)})
    game = Game.objects.select_related('outline').get(index=game_index)
    size = int(math.sqrt(len(game.board)))
    outline = Outline(index=1, board=(0,0,1,1,2,3,0,0,1,2,3,0,4,1,2,3,3,4,1,2,3,4,4,4,2))
    outline = game.outline

    if settings.DEBUG:
        solution = solve(board=game.board, outline=outline.board, disabled_nodes=game.disabled_nodes)
        #assert len(solution) == game.moves_min_num
        print(solution)

    bordered_board = init_borders(outline=outline.board, css_variable='cell-width', board=game.board)
    bordered_outline = init_borders(outline=outline.board, css_variable='outline-cell-width')
    if date is None:
        next_puzzle_url = None
    else:
        kwargs = dict()
        days_to_today = (today_date - date).days
        if days_to_today > 1:
            kwargs['date'] = current_date + datetime.timedelta(days=1)
        next_puzzle_url = None if days_to_today < 1 else reverse('rotatly', kwargs=kwargs)
    return render(request, 'game.html',
                  dict(size=size,
                       game=game,
                       board=bordered_board,
                       outline=bordered_outline,
                       outline_dumped=json.dumps(outline.board),
                       pre_moves=pre_moves,
                       pre_moves_dumped=json.dumps(pre_moves),
                       is_solved=is_solved(game.board, outline.board, pre_moves, game.disabled_nodes),
                       nodes=[[(e, game.disabled_nodes.get(str(e), dict())) for e in range(i, i + size - 1)] for i in
                              range(1, (size - 1) ** 2, size - 1)],
                       moves_max_num=game.moves_min_num * 10,
                       cw_symbol=CW_SYMBOLS[0],
                       ccw_symbol=CCW_SYMBOLS[0],
                       archived=date is not None,
                       current_date=current_date.strftime('%B %d, %Y'),

                       today_url=reverse('rotatly'),
                       canonical_url=reverse('rotatly', args=(current_date,)),
                       previous_puzzle_url=None if game_index == 1 else reverse('rotatly', kwargs={
                           'date': current_date - datetime.timedelta(days=1)}),
                       next_puzzle_url=next_puzzle_url,
                       debug=settings.DEBUG))


def track(request):
    if not settings.DEBUG:
        from django.core.mail import send_mail
        send_mail('Rotatly',
                  str(request.GET),
                  None,
                  [a[1] for a in settings.ADMINS])
    return JsonResponse({})
