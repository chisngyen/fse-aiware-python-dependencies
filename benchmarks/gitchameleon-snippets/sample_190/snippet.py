from sympy.physics.mechanics import *
import sympy.physics.mechanics

def custom_body(rigid_body_text: str, particle_text: str) -> tuple[sympy.physics.mechanics.RigidBody, sympy.physics.mechanics.Particle]:
    return
RigidBody(rigid_body_text), Particle(particle_text)

# --- test ---
rigid_body_text = "rigid_body"
particle_text = "particle"
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    exp1, exp2 = custom_body(rigid_body_text, particle_text)
    assert exp1.name == rigid_body_text
    assert exp2.name == particle_text
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
