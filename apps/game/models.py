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
