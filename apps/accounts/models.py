import uuid

from django.contrib.auth.models import User
from django.db.models import Model, OneToOneField, UUIDField, EmailField, DateTimeField, CASCADE
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Gamer(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(User, related_name='gamer', on_delete=CASCADE)


class EmailActivation(Model):
    id = UUIDField(primary_key=True,
                   default=uuid.uuid4,
                   editable=False)
    email = EmailField(verbose_name=_('Email address'), unique=True)
    date_issued = DateTimeField(default=timezone.now)
