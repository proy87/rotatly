import datetime
import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.game.constants import START_DATE
from apps.game.creation import create_daily_puzzle, get_outline_for_index, get_or_create_default_outline
from apps.game.models import Daily, Outline


class Command(BaseCommand):
    help = "Create missing daily puzzles from the start date through today."

    def add_arguments(self, parser):
        parser.add_argument("--outline-id", type=int, help="Outline id to use.")
        parser.add_argument("--max-tries", type=int, default=200, help="Max random board attempts per day.")
        parser.add_argument("--reset", action="store_true", help="Delete existing daily puzzles before seeding.")

    def handle(self, *args, **options):
        outline_id = options.get("outline_id")
        max_tries = options.get("max_tries")
        reset = options.get("reset")

        if outline_id:
            try:
                outline = Outline.objects.get(id=outline_id)
            except Outline.DoesNotExist as exc:
                raise CommandError(f"Outline id {outline_id} does not exist.") from exc
            outline_list = None
        else:
            outline_list = list(Outline.objects.order_by("index"))
            outline = get_or_create_default_outline()

        release_offset_hours = 0 if settings.DEBUG else 5
        today_date = datetime.datetime.now() - datetime.timedelta(hours=release_offset_hours)
        days_passed = (today_date - START_DATE).days
        if days_passed <= 0:
            raise CommandError("Start date is in the future.")

        board_template = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
        retryable_errors = {"The puzzle is unsolvable.", "The puzzle is already solved."}

        if reset:
            Daily.objects.all().delete()

        created = 0
        skipped = 0
        last_error = None

        for index in range(1, days_passed + 1):
            if Daily.objects.filter(index=index).exists():
                skipped += 1
                continue

            outline_for_day = outline
            if outline_list:
                outline_for_day = outline_list[(index - 1) % len(outline_list)]

            for _ in range(max_tries):
                board = board_template[:]
                random.shuffle(board)
                game, error = create_daily_puzzle(
                    outline=outline_for_day.board,
                    board=board,
                    fixed_areas={},
                    disabled_nodes={},
                    index=index,
                )
                if game:
                    created += 1
                    break
                last_error = error
                if error not in retryable_errors:
                    raise CommandError(error or f"Failed to create puzzle for index {index}.")
            else:
                raise CommandError(last_error or f"Failed to create puzzle for index {index} after retries.")

        api_url = settings.SITE_DOMAIN + reverse("api-puzzle-date", kwargs={"date": today_date})
        self.stdout.write(
            self.style.SUCCESS(
                f"Daily puzzles ready. created={created} skipped={skipped} total={days_passed}. "
                f"Latest: {api_url}"
            )
        )
