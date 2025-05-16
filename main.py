import json
import gradio as gr


def fetch_parameters() -> list:
    with open("parameters.json") as file:
        params = json.load(file)

    rendered = []
    for param in params.items():
        if param[1]["type"] == "text":
            if param[1]["possible_values"] is None:
                rendered.append("text")
            else:
                rendered.append(gr.Radio(param[1]["possible_values"]))
        elif param[1]["type"] == "number":
            rendered.append("number")
        else:
            raise KeyError

    return rendered


def debug(
    cap_shape: str,
    cap_surface: str,
    cap_color: str,
    does_bruise_or_bleed: str,
    gill_attachment: str,
    gill_color: str,
    stem_color: str,
    has_ring: str,
    ring_type: str,
    habitat: str,
    season: str,
    cap_diameter: float,
    stem_hight: float,
    stem_width: float
) -> str:
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
