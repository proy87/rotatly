import datetime
import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.game.constants import START_DATE
from apps.game.creation import create_daily_puzzle, get_outline_for_index, get_or_create_default_outline
from apps.game.models import Outline


class Command(BaseCommand):
    help = "Create a daily puzzle for a given date using create-mode validation."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD.")
        parser.add_argument("--index", type=int, help="Daily index to create.")
        parser.add_argument("--outline-id", type=int, help="Outline id to use.")
        parser.add_argument("--max-tries", type=int, default=200, help="Max random board attempts.")

    def handle(self, *args, **options):
        date_str = options.get("date")
        index = options.get("index")
        outline_id = options.get("outline_id")
        max_tries = options.get("max_tries")

        if date_str and index is not None:
            raise CommandError("Use either --date or --index, not both.")

        if date_str:
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError as exc:
                raise CommandError("Invalid --date format (expected YYYY-MM-DD).") from exc
            index = (date - START_DATE).days
        elif index is not None:
            if index <= 0:
                raise CommandError("Index must be a positive integer.")
            date = START_DATE + datetime.timedelta(days=index)
        else:
            release_offset_hours = 0 if settings.DEBUG else 5
            date = datetime.datetime.now() - datetime.timedelta(hours=release_offset_hours)
            index = (date - START_DATE).days

        if index <= 0:
            raise CommandError("Date is before start date.")

        if outline_id:
            try:
                outline = Outline.objects.get(id=outline_id)
            except Outline.DoesNotExist as exc:
                raise CommandError(f"Outline id {outline_id} does not exist.") from exc
        else:
            outline = get_outline_for_index(index) if index else get_or_create_default_outline()

        board_template = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
        retryable_errors = {"The puzzle is unsolvable.", "The puzzle is already solved."}

        last_error = None
        for _ in range(max_tries):
            board = board_template[:]
            random.shuffle(board)
            game, error = create_daily_puzzle(
                outline=outline.board,
                board=board,
                fixed_areas={},
                disabled_nodes={},
                index=index,
            )
            if game:
                api_url = settings.SITE_DOMAIN + reverse("api-puzzle-date", kwargs={"date": date})
                self.stdout.write(self.style.SUCCESS(f"Created daily puzzle: {api_url}"))
                return
            last_error = error
            if error not in retryable_errors:
                raise CommandError(error or "Failed to create puzzle.")

        raise CommandError(last_error or "Failed to create puzzle after retries.")
