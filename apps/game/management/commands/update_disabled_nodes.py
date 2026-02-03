from django.conf import settings
from django.core.management.base import BaseCommand
from apps.game.models import Daily, Custom
from apps.game.solver import solve
from apps.game.board import get_nodes
from apps.game.utils import encode


class Command(BaseCommand):
    help = 'Update disabled nodes'

    def handle(self, *args, **options):
        for klass in (Daily, Custom):
            for game in klass.objects.all():
                disabled_nodes = game.disabled_nodes
                game.disabled_nodes = [g for g in game.disabled_nodes if g[0] < 10]
                for i in range(10, 18):
                    game.disabled_nodes.append([i, True, True])
                game.disabled_nodes = sorted(game.disabled_nodes, key=lambda x: x[0])
                if game.disabled_nodes != disabled_nodes:
                    print(klass, game.index)
                    game.save()

        for klass in (Daily, Custom):
            for game in klass.objects.all():
                board = encode(game.board, game.fixed_areas_as_int)
                outline_board = encode(game.outline.board, game.fixed_areas_as_int, for_outline=True)
                nodes = get_nodes(4,4, game.disabled_nodes_as_dict)
                solution = solve(board=board,
                                 outline=outline_board,
                                 nodes=nodes,
                                 fixed_areas=game.fixed_areas_as_int)

                if len(solution) != game.moves_min_num:
                    print(klass, game.index, len(solution), game.moves_min_num)
                    game.moves_min_num = len(solution)
                    game.save()