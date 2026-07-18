from sympy.physics.mechanics import Body, PinJoint
import sympy.physics.mechanics

def custom_pinJoint(parent: sympy.physics.mechanics.Body, child: sympy.physics.mechanics.Body) -> sympy.physics.mechanics.PinJoint:
    return
PinJoint('pin', parent, child, parent_point=parent.frame.x,child_point=-child.frame.x)

# --- test ---
parent, child = Body('parent'), Body('child')
pin = custom_pinJoint(parent, child)
expect1 = parent.frame.x
expect2 = -child.frame.x

assert pin.parent_point.pos_from(parent.masscenter) == expect1
assert pin.child_point.pos_from(child.masscenter) == expect2
