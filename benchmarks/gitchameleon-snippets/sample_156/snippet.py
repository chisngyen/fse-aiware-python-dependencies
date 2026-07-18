import re
from jinja2 import Environment, pass_eval_context
from markupsafe import Markup, escape
from typing import Callable, Union
from jinja2.runtime import EvalContext

def get_output(env, filter_fn):
    env.filters['nl2br'] = filter_fn
    template = env.from_string('{{ text | nl2br }}')
    output = template.render(text='Hello World')
    return output

def nl2br_core(eval_ctx, value):
    br = '<br>Hello</br>'
    if eval_ctx.autoescape:
        value = escape(value)
        br = Markup(br)
    result = re.sub(r'Hello', br, value)
    return Markup(result) if eval_ctx.autoescape else result

def solution() -> Callable[[EvalContext, str], Markup | str]:

    @pass_eval_context
    def nl2br(eval_ctx, value):
        return nl2br_core(eval_ctx, value)
    
    return nl2br

# --- test ---

nl2br_filter = solution()

env = Environment(autoescape=True)
output = get_output(env,nl2br_filter)
expected = '<br>Hello</br> World'

assert output == expected
