import gradio as gr
def process_image(image):
    return "Processed"

iface = gr.Interface
(fn=process_image, inputs=gr.inputs.Image(), outputs=gr.outputs.Textbox())

# --- test ---
assertion_value = type(iface.input_components[0])==type(gr.inputs.Image()) and type(iface.output_components[0])==type(gr.outputs.Textbox()) or type(iface.input_components[0])==type(gr.components.Image()) and type(iface.output_components[0])==type(gr.components.Textbox())
assert assertion_value
