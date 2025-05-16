import json
import gradio as gr


def fetch_parameters():
    with open("parameters.json") as file:
        params = json.load(file)

    parameters = []

    for param_key, param_info in params.items():
        parameters.append({
            "name": param_key,
            "type": param_info["type"],
            "values": param_info.get("possible_values"),
            "image": param_info.get("image"),
            "prerequisites": param_info.get("prerequisites")
        })

    return parameters


def create_component(param):
    image = gr.Image(param["image"], interactive=False, show_label=False, height=100) \
        if param["image"] is not None else None

    kwargs = {"label": " ".join(param["name"].split("-")).capitalize()}

    if param["type"] == "text":
        return (image, gr.Textbox(**kwargs)) \
            if param["values"] is None else (image, gr.Radio(param["values"], **kwargs))

    if param["type"] == "number":
        return (image, gr.Number(**kwargs))

    if param["type"] == "bool":
        return (image, gr.Checkbox(**kwargs))

    raise KeyError(f"Invalid type {param['type']}")


def setup_visibility(components, connections):
    for lhs, rhs in connections:
        parent = components[lhs]
        child = list(map(lambda x: x, components[rhs]))

        for element in child:
            element.visible = False

        parent[1].change(
            lambda x, child=child:
                [gr.update(visible=x) for _ in child],
            inputs=parent[1],
            outputs=child
        )


def debug(*args):
    return "A-OK"


def main():
    with gr.Blocks() as demo:
        components = {}
        connections = []

        for param in fetch_parameters():
            with gr.Group():
                image, element = create_component(param)
                components[param["name"]] = (image, element)

                if param["prerequisites"]:
                    connections.extend((parent, param["name"])
                                       for parent in param["prerequisites"])

        setup_visibility(components, connections)

        gr.Button("Submit").click(
            fn=debug,
            inputs=[comp[1] for comp in components.values()],
            outputs=gr.Textbox(label="Result")
        )

    demo.launch()


if __name__ == "__main__":
    main()
