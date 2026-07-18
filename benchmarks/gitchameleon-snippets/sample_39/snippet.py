import gradio as gr
def display_image():
    return "https://image_placeholder.com/42"

iface = gr.Interface
(fn=display_image, inputs=[], outputs=gr.Image())

# --- test ---
assertion_value = type(gr.Image()) == type(iface.output_components[0])
assert assertion_value
