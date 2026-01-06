from django.db import models


class Outline(models.Model):
    index = models.PositiveIntegerField()
    board = models.JSONField()


class Game(models.Model):
    index = models.PositiveIntegerField()
    board = models.JSONField()
    encoded_board = models.JSONField()
    moves_min_num = models.PositiveIntegerField()
    disabled_nodes = models.JSONField(default=dict)
    outline = models.ForeignKey(Outline, on_delete=models.CASCADE)
    fixed_areas = models.JSONField(default=dict)
