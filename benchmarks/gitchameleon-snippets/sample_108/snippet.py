import django
from django.conf import settings
from django.db import models

settings.configure()
django.setup()

color = models.TextChoices('Color', 'RED GREEN BLUE')

class MyModel(models.Model):
    class Meta:
        app_label = 'myapp'
    color = models.CharField(max_length=5,
 choices=color.choices)

# --- test ---


field_choices = MyModel._meta.get_field('color').choices

expected_choices = [('RED', 'Red'), ('GREEN', 'Green'), ('BLUE', 'Blue')]

assert field_choices == expected_choices
