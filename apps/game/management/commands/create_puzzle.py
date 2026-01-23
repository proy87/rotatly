import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.game.creation import create_custom_puzzle, get_or_create_default_outline
from apps.game.models import Outline


class Command(BaseCommand):
    help = "Create a custom puzzle using create-mode validation."

    def add_arguments(self, parser):
        parser.add_argument("--outline-id", type=int, help="Outline id to use.")
        parser.add_argument("--max-tries", type=int, default=200, help="Max random board attempts.")

    def handle(self, *args, **options):
        outline_id = options.get("outline_id")
        max_tries = options.get("max_tries")

        if outline_id:
            try:
                outline = Outline.objects.get(id=outline_id)
            except Outline.DoesNotExist as exc:
                raise CommandError(f"Outline id {outline_id} does not exist.") from exc
        else:
            outline = get_or_create_default_outline()

        board_template = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
        retryable_errors = {"The puzzle is unsolvable.", "The puzzle is already solved."}

        last_error = None
        for _ in range(max_tries):
            board = board_template[:]
            random.shuffle(board)
            game, error = create_custom_puzzle(
                outline=outline.board,
                board=board,
                fixed_areas={},
                disabled_nodes={},
            )
            if game:
                url = settings.SITE_DOMAIN + reverse("custom", args=(game.index,))
                self.stdout.write(self.style.SUCCESS(f"Created puzzle: {url}"))
                return
            last_error = error
            if error not in retryable_errors:
                raise CommandError(error or "Failed to create puzzle.")

        raise CommandError(last_error or "Failed to create puzzle after retries.")
