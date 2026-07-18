import gradio as gr
def render_quadratic_formula():
     pass


interface = gr.Interface(fn=render_quadratic_formula, inputs=[], outputs = "text")

def render_quadratic_formula():
    formula =
"$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$"
    return formula

# --- test ---
assertion_value = render_quadratic_formula().startswith("$") and render_quadratic_formula().endswith("$") 
assert assertion_value
