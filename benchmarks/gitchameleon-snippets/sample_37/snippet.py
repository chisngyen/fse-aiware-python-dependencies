import gradio as gr
def render_quadratic_formula():
    formula = "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"
    return formula

interface = gr.Chatbot
(fn=render_quadratic_formula, latex_delimiters=("$$", "$$"))

# --- test ---
assertion_value = not render_quadratic_formula().startswith("$") and not render_quadratic_formula().endswith("$") and "$" in interface.latex_delimiters[0] and  "$" in interface.latex_delimiters[1]
assert assertion_value
