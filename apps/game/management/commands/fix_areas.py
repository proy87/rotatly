from django.conf import settings
from django.core.management.base import BaseCommand
from apps.game.models import Daily
from apps.game.utils import encode
from apps.game.solver import solve, is_solved, Block, rotate_block

class Command(BaseCommand):
    def handle(self, *args, **options):
        for o in Daily.objects.all():
            if len(o.fixed_areas) != 4:
                outline = o.outline
                solution = solve(board=encode(o.board, o.fixed_areas_as_int),
                                 outline=encode(outline.board, o.fixed_areas_as_int, mode='outline'),
                                 disabled_nodes=o.disabled_nodes_as_int,
                                 fixed_areas=o.fixed_areas_as_int)
                blocks = {block.index: block for block in Block.get_blocks(4, 4, o.disabled_nodes_as_int)}
                start = tuple(o.board)
                for index, cw in solution:
                    block = blocks[index]
                    start = rotate_block(start, block.indices, None, cw == 'CW')
                print(o.index)
                areas = {}
                next_id = 1
                for item in start:
                    if item not in areas.values():
                        areas[f"{next_id}"] = item
                        next_id += 1
                o.fixed_areas = areas
                o.save()
