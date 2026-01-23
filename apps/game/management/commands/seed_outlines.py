from django.core.management.base import BaseCommand
from django.db import models

from apps.game.models import Outline
from apps.game.outline_generator import generate_outline_boards


class Command(BaseCommand):
    help = "Seed Outline rows using all possible tetromino tilings of a 4x4 board."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing outlines before seeding.")

    def handle(self, *args, **options):
        reset = options.get("reset")
        if reset:
            Outline.objects.all().delete()

        existing_boards = set()
        if not reset:
            for board in Outline.objects.values_list("board", flat=True):
                existing_boards.add(tuple(board))

        outlines = generate_outline_boards()
        next_index = Outline.objects.aggregate(max_index=models.Max("index")).get("max_index") or 0
        created = 0
        for board in outlines:
            if board in existing_boards:
                continue
            next_index += 1
            Outline.objects.create(index=next_index, board=list(board))
            created += 1

        total = Outline.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Outlines ready. created={created} total={total}."))
