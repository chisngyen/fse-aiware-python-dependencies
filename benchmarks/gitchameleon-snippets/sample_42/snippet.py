import gradio as gr

def get_selected_options(options):
    return f"Selected options: {options}"

selection_options = ["angola", "pakistan", "canada"]

iface = gr.Interface(get_selected_options, inputs =
gr.Dropdown(selection_options, multiselect=True), outputs = 'text')

# --- test ---
assertion_value = (type(iface.input_components[0]) == gr.Dropdown and iface.input_components[0].multiselect == True ) or type(iface.input_components[0]) == gr.CheckboxGroup
assert assertion_value
