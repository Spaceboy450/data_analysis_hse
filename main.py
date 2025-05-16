import json
import gradio as gr


def fetch_parameters() -> list:
    with open("parameters.json") as file:
        params = json.load(file)

    rendered = []
    for param in params.items():
        name = " ".join(param[0].split("-")).capitalize()
        value_type = param[1]["type"]

        if value_type == "text":
            values = param[1]["possible_values"]
            if values is None:
                rendered.append(gr.Textbox(label=name, lines=1))
            else:
                rendered.append(gr.Radio(values, label=name))
        elif value_type == "number":
            rendered.append(gr.Number(label=name))
        else:
            raise KeyError

    return rendered


def debug(*args) -> str:
    return "A-OK"


def main():
    demo = gr.Interface(
        fn=debug,
        inputs=fetch_parameters(),
        outputs=["text"]
    )
    demo.launch()


if __name__ == "__main__":
    main()
