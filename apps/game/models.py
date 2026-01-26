from django.conf import settings
from django.db import models
from django.utils.functional import cached_property


class Outline(models.Model):
    index = models.PositiveIntegerField()
    board = models.JSONField()


class Game(models.Model):
    board = models.JSONField()
    encoded_board = models.JSONField()
    moves_min_num = models.PositiveIntegerField()
    disabled_nodes = models.JSONField(default=dict, blank=True)
    outline = models.ForeignKey(Outline, on_delete=models.CASCADE)
    fixed_areas = models.JSONField(default=dict, blank=True)

    @cached_property
    def disabled_nodes_as_int(self):
        return {int(k): v for k, v in self.disabled_nodes.items()}

    @cached_property
    def fixed_areas_as_int(self):
        return {int(k): int(v) for k, v in self.fixed_areas.items()}

    class Meta:
        abstract = True


class Daily(Game):
    index = models.PositiveIntegerField(db_index=True)


class Custom(Game):
    index = models.CharField(max_length=8, db_index=True)


class PuzzleAttempt(models.Model):
    DAILY = 'daily'
    CUSTOM = 'custom'
    PUZZLE_TYPES = (
        (DAILY, 'Daily'),
        (CUSTOM, 'Custom'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='puzzle_attempts')
    puzzle_type = models.CharField(max_length=10, choices=PUZZLE_TYPES)
    daily = models.ForeignKey(Daily, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    custom = models.ForeignKey(Custom, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    moves = models.PositiveIntegerField()
    seconds = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
