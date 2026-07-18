from django.conf import settings
from django.forms.models import BaseModelFormSet
from django.forms.renderers import get_default_renderer
from django.forms import Form

settings.configure()
def save_existing(formset: BaseModelFormSet, form : Form, obj:str) -> None:
    return formset.save_existing(form=form,instance=obj)

# --- test ---


class DummyForm:
    def save(self, commit=True):
        return 'dummy_instance_value_result'

class MyFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.renderer = get_default_renderer()
        super().__init__(*args, **kwargs)
fs5 = MyFormSet(queryset=[])
result = save_existing(formset=fs5,form=DummyForm(), obj='dummy_str')
assertion_result = result == 'dummy_instance_value_result'
assert assertion_result
