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

    moves_re = re.findall(fr'([1-9])\s*([{CW_SYMBOLS}{CCW_SYMBOLS}])', request.GET.get('moves', ''))
    pre_moves = [(int(k), v in CW_SYMBOLS) for k, v in moves_re]
    game = Game.objects.select_related('outline').get(index=game_index)
    outline = game.outline
    if settings.DEBUG:
        solution = solve(board=game.board, outline=outline.board, disabled_nodes=game.disabled_nodes)
        print(solution)

    bordered_board = init_borders(outline=outline.board, css_variable='cell-width', board=game.board)
    bordered_outline = init_borders(outline=outline.board, css_variable='cell-width-outline')
    if date is None:
        next_puzzle_url = None
    else:
        kwargs = dict()
        days_to_today = (today_date - date).days
        if days_to_today > 1:
            kwargs['date'] = current_date + datetime.timedelta(days=1)
        next_puzzle_url = None if days_to_today < 1 else reverse('rotatly', kwargs=kwargs)
    return render(request, 'game.html',
                  dict(game=game,
                       board=bordered_board,
                       outline=bordered_outline,
                       outline_dumped=json.dumps(outline.board),
                       pre_moves=pre_moves,
                       pre_moves_dumped=json.dumps(pre_moves),
                       is_solved=is_solved(game.board, outline.board, pre_moves, game.disabled_nodes),
                       nodes=[[(e, game.disabled_nodes.get(str(e), dict())) for e in range(i, i + 3)] for i in
                              range(1, 9, 3)],
                       moves_max_num=game.moves_min_num * 10,
                       cw_symbol=CW_SYMBOLS[0],
                       ccw_symbol=CCW_SYMBOLS[0],
                       archived=date is not None,
                       current_date=current_date.strftime('%B %d, %Y'),

                       today_url=reverse('rotatly'),
                       canonical_url=reverse('rotatly', args=(current_date,)),
                       previous_puzzle_url=None if game_index == 1 else reverse('rotatly', kwargs={
                           'date': current_date - datetime.timedelta(days=1)}),
                       next_puzzle_url=next_puzzle_url))


def track_rotatly(request):
    if not settings.DEBUG:
        from django.core.mail import send_mail
        send_mail('Rotatly',
                  str(request.GET),
                  None,
                  [a[1] for a in settings.ADMINS])
    return JsonResponse({})
