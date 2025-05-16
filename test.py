import json
import gradio as gr

def fetch_parameters() -> list:
    with open("parameters.json") as file:
        params = json.load(file)
    
    parameters = []
    for param_key, param_info in params.items():
        parameters.append({
            "name": " ".join(param_key.split("-")).capitalize(),
            "type": param_info["type"],
            "values": param_info.get("possible_values"),
            "image": f"resources/{param_key}.jpg"  # Update path logic as needed
        })
    return parameters

def debug(*args) -> str:
    return "A-OK"

def main():
    with gr.Blocks() as demo:
        gr.Markdown("## Parameter Configuration")
        input_components = []
        
        for param in fetch_parameters():
            with gr.Group():
                # Create image once in the Blocks context
                gr.Image(param["image"], 
                        interactive=False, 
                        show_label=False, 
                        height=100)
                
                # Create input component
                if param["type"] == "text":
                    if param["values"] is None:
                        inp = gr.Textbox(label=param["name"], lines=1)
                    else:
                        inp = gr.Radio(param["values"], label=param["name"])
                elif param["type"] == "number":
                    inp = gr.Number(label=param["name"])
                else:
                    raise KeyError(f"Invalid type {param['type']}")
                
                input_components.append(inp)
        
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Result")
        submit_btn.click(fn=debug, inputs=input_components, outputs=output)

    demo.launch()

if __name__ == "__main__":
    main()
