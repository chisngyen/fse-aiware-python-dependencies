from sympy import symbols
from sympy.physics.mechanics import (
Particle, PinJoint, PrismaticJoint, RigidBody)
import sympy
import sympy.physics.mechanics

def custom_motion(wall: sympy.physics.mechanics.RigidBody, slider: sympy.physics.mechanics.PrismaticJoint, pin: sympy.physics.mechanics.PinJoint) -> sympy.Matrix:
    from sympy.physics.mechanics import
System
    system = System.from_newtonian(wall)
    system.add_joints(slider, pin)
    return system.form_eoms()

# --- test ---
l = symbols("l")
wall = RigidBody("wall")
cart = RigidBody("cart")
pendulum = RigidBody("Pendulum")
slider = PrismaticJoint("s", wall, cart, joint_axis=wall.x)
pin = PinJoint("j", cart, pendulum, joint_axis=cart.z,
               child_point=l * pendulum.y)

from sympy import symbols, Function, Derivative, Matrix, sin, cos
t = symbols('t')
l, Pendulum_mass, cart_mass, Pendulum_izz = symbols('l Pendulum_mass cart_mass Pendulum_izz')

q_j = Function('q_j')
u_j = Function('u_j')
u_s = Function('u_s')
M = Matrix([
    [Pendulum_mass*l*u_j(t)**2*sin(q_j(t)) - Pendulum_mass*l*cos(q_j(t))*Derivative(u_j(t), t)
     - (Pendulum_mass + cart_mass)*Derivative(u_s(t), t)],
    [-Pendulum_mass*l*cos(q_j(t))*Derivative(u_s(t), t)
     - (Pendulum_izz + Pendulum_mass*l**2)*Derivative(u_j(t), t)]
])
assert custom_motion(wall,slider, pin) == M
