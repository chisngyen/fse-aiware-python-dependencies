import gradio as gr
def process_image(image):
    return "Processed"

iface = gr.Interface
(fn=process_image, inputs=gr.Image(), outputs=gr.Label())

# --- test ---
assertion_value = type(iface.input_components[0])==type(gr.Image()) and type(iface.output_components[0])==type(gr.Label())
assert assertion_value
