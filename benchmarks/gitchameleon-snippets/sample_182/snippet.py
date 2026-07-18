from sympy.physics.mechanics import Body, PinJoint
import sympy.physics.mechanics
import sympy as sp


def custom_pinJoint_connect(parent: sympy.physics.mechanics.Body, child: sympy.physics.mechanics.Body) -> sympy.physics.mechanics.PinJoint:
    return
PinJoint('pin', parent, child, parent_point=parent.frame.x,child_point=-child.frame.x)

# --- test ---

parent, child = Body('parent'), Body('child')
pin = custom_pinJoint_connect(parent, child)
assertion_value = isinstance(pin.coordinates, sp.Matrix)
assert assertion_value
assertion_value = isinstance(pin.speeds, sp.Matrix)
assert assertion_value
