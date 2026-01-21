from django.conf import settings
from django.core.management.base import BaseCommand
from apps.game.models import *


import urllib.request
import json


class Command(BaseCommand):
    help = 'Populate'

    def handle(self, *args, **options):
        url = "https://www.emathhelp.net/data.txt"

        with urllib.request.urlopen(url) as response:
            # Read response and decode bytes to string
            data_str = response.read().decode('utf-8')

            # Parse JSON string into Python dict/list
            data = json.loads(data_str)

            for item in data:
                if item['model'] == 'rotatly.outline':
                    obj = Outline()
                    for k, v in item['fields'].items():
                        setattr(obj, k, v)
                    obj.save()
                elif item['model'] == 'rotatly.daily':
                    obj = Daily()
                    for k, v in item['fields'].items():
                        if k == 'outline':
                            obj.outline = Outline.objects.get(pk=v)
                        else:
                            setattr(obj, k, v)
                    obj.save()
