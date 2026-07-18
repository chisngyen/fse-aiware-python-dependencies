import gradio as gr
def display_image():
    return "https://image_placeholder.com/42"

iface = gr.Interface
(fn=display_image, inputs=[], outputs=gr.Image(show_share_button=False))

# --- test ---
assertion_value = iface.output_components[0].show_share_button==False 
assert assertion_value
