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

        # Скрываем все child-компоненты по умолчанию
        for element in child:
            element.visible = False

        # Устанавливаем условие видимости
        parent[1].change(
            lambda x, child=child: [
                gr.update(visible=(x == "true")) for _ in child
            ],
            inputs=parent[1],
            outputs=child
        )



from data_processing import DataPreprocessor
import joblib
import pandas as pd
from catboost import CatBoostClassifier

def main():
    with gr.Blocks() as demo:
        components = {}
        connections = []

        for param in fetch_parameters():
            with gr.Group():
                components[param["name"]] = create_component(param)
                if param["prerequisites"]:
                    connections.extend((parent, param["name"])
                                       for parent in param["prerequisites"])

        def debug(*args):

            data = {
                "cap-shape": {
                    "possible_values": ["Колокольчатая","Коническая", "Выпуклая", "Плоская", "С выступом",  "Вогнутая"]
                },
                "cap-surface": {
                    "possible_values": ["Волокнистая",  "С бороздками",  "Чешуйчатая", "Гладкая"]
                },
                "cap-color": {
                    "possible_values": ["Коричневый", "Охристый", "Коричнево-оранжевый", "Серый","Зеленый", "Розовый", "Фиолетовый", "Красный", "Белый",
                                        "Желтый"]
                },
                "does-bruise-or-bleed": {
                    "possible_values": ["Да", "Нет"]
                },
                "gill-attachment": {
                    "possible_values": ["Приросшие", "Нисходящие (сползают по ножке вниз)", "Свободные", "Приросшие к ножке зубцом"]
                },
                "gill-color": {
                     "possible_values": ["Черный","Коричневый", "Желтовато-коричневый","Шоколадный", "Серый","Зеленый", "Оранжевый" ,"Розовый", "Фиолетовый", "Красный", "Белый",
                                        "Желтый"]
                },
                "stem-color": {
                     "possible_values": ["Коричневый", "Охристый", "Коричнево-оранжевый", "Серый","Оранжевый", "Розовый",  "Красный", "Белый",
                                        "Желтый"]
                },
                "has-ring": {
                    "possible_values": ["true", "false"]
                },
                "ring-type": {
                    "possible_values": ["Паутинистое", "Исчезающее", "Плоское", "Крупное", "Отсутсвует", "Юбкообразное", "Раструбовидное", "Кольцевая зона или след"],
                },
                "habitat": {
                    "possible_values": ["Трава", "Лиственная подстилка", "Луга", "Тропинки", "Город", "Свалки", "Леса"]
                },
                "season": {
                    "possible_values": ["Лето", "Осень", "Зима", "Весна"]
                }
            }

            letters_map = {
                'cap-shape': ['b', 'c', 'x', 'f', 'k', 's'],
                'cap-surface': ['f', 'g', 'y', 's'],
                'cap-color': ['n', 'b', 'c', 'g', 'r', 'p', 'u', 'e', 'w', 'y'],
                'does-bruise-or-bleed': ['f', 't'],
                'gill-attachment': ['a', 'd', 'f', 'n'],
                'gill-color': ['k', 'n', 'b', 'h', 'g', 'r', 'o', 'p', 'u', 'e', 'w', 'y'],
                'stem-color': ['n', 'b', 'c', 'g', 'o', 'p', 'e', 'w', 'y'],
                'has-ring': ['f', 't'],
                'ring-type': ['c', 'e', 'f', 'l', 'n', 'p', 's', 'z'],
                'habitat': ['g', 'l', 'm', 'p', 'u', 'w', 'd'],
                'season': ['a', 'w', 'u', 's']
            }

            def get_letter_by_value(feature: str, value) -> str | int | None:
                if isinstance(value, int):
                    return value

                if feature not in data or feature not in letters_map:
                    return None

                possible_values = data[feature]["possible_values"]
                letters = letters_map[feature]

                if value not in possible_values:
                    return None

                index = possible_values.index(value)
                if index >= len(letters):
                    return None

                return letters[index]

            model = CatBoostClassifier()
            model.load_model("notes/classifier.cbm")

            preprocessor = joblib.load("my_preprocessor.pkl")

            param = list(components.keys())

            input_dict = {name: get_letter_by_value(name, value) for name, value in zip(param, args)}
            data_dict = pd.DataFrame(input_dict, index=[0])
            pd.set_option('display.max_columns', None)
            print(data_dict)
            X_prediction = preprocessor.transform(data_dict)
            print(X_prediction)

            prediction = model.predict(X_prediction)

            return str(prediction[0])

        setup_visibility(components, connections)

        gr.Button("Submit").click(
            fn=debug,
            inputs=[comp[1] for comp in components.values()],
            outputs=gr.Textbox(label="Result")
        )

    demo.launch()


if __name__ == "__main__":
    main()
