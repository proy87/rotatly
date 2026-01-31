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
                new_disabled_nodes = []
                if isinstance(disabled_nodes, dict):
                    for k, v in disabled_nodes.items():
                        new_disabled_nodes.append((int(k), v['cw'], v['ccw']))

                    # 69 70 71 72 73 74 75
                    if klass == Daily and (game.index < 69 or game.index > 75):
                        for i in range(10, 18):
                            new_disabled_nodes.append((i, True, True))
                    new_disabled_nodes = sorted(new_disabled_nodes, key=lambda x: x[0])
                    game.disabled_nodes = new_disabled_nodes
                    game.save()
                else:
                    print(klass)
                    print(disabled_nodes)

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
