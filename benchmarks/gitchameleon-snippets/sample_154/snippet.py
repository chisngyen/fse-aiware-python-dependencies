import jinja2 
from jinja2.runtime import Context
from typing import Callable

def setup_environment(filtername: str,filter) -> jinja2.Environment:
    env = jinja2.Environment()
    env.filters[filtername] = filter
    return env

def solution() -> Callable[[Context, str], str]:
    @jinja2.pass_context
    def greet(ctx, name):
        prefix = ctx.get('prefix', 'Hello')
        return f'{prefix}, {name}!'
        
    return greet

# --- test ---
greet = solution()
env = setup_environment('greet',greet)
template = env.from_string('''
{{ 'World'| greet }}''')
assertion_results = 'Hi, World!' in template.render(prefix='Hi')
assert assertion_results 
assertion_results = 'Hello, World!' in template.render()
assert assertion_results
