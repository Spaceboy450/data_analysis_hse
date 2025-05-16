import json
import gradio as gr


def fetch_parameters() -> list:
    with open("parameters.json") as file:
        params = json.load(file)

    has_image = ["cap-shape", "cap-surface", "gill-attachment", "ring-type"]
    parameters = []

    for param_key, param_info in params.items():
        parameters.append({
            "name": " ".join(param_key.split("-")).capitalize(),
            "type": param_info["type"],
            "values": param_info.get("possible_values"),
            "image": f"resources/{param_key}.jpg" if param_key in has_image else None
        })

    return parameters


def deduce_block_type(param: dict):
    if param["image"] is not None:
        image = gr.Image(param["image"], interactive=False, show_label=False, height=100)
    else:
        image = None

    if param["type"] == "text":
        if param["values"] is None:
            return (image, gr.Textbox(label=param["name"], lines=1))
        return (image, gr.Radio(param["values"], label=param["name"]))

    if param["type"] == "number":
        return (image, gr.Number(label=param["name"]))

    if param["type"] == "bool":
        return (image, gr.Checkbox(label=param["name"]))

    raise KeyError(f"Invalid type {param['type']}")


def debug(*args) -> str:
    return "A-OK"


def main():
    with gr.Blocks() as demo:
        components = []

        has_ring = None
        ring_type = None
        ring_type_image = None

        for param in fetch_parameters():
            with gr.Group():
                image, input = deduce_block_type(param)

                if param["name"] == "Has ring":
                    has_ring = input
                elif param["name"] == "Ring type":
                    ring_type = input
                    ring_type_image = image

                components.append(input)

        ring_type.visible = False
        ring_type_image.visible = False

        has_ring.change(
            lambda x: [gr.update(visible=x), gr.update(visible=x)],
            inputs=has_ring,
            outputs=[ring_type_image, ring_type]
        )

        submit_button = gr.Button("Submit")
        output = gr.Textbox(label="Result")
        submit_button.click(fn=debug, inputs=components, outputs=output)

    demo.launch()


if __name__ == "__main__":
    main()
