# -*- coding: utf-8 -*-
"""
Python project. Binary classification of mushrooms.

Performed by: Andreev Alexander, Chapaykin Arseniy, Ro Alexander, Shmelev Anton 
"""

import json
from data_processing import DataPreprocessor # pylint: disable=unused-import
import joblib
from catboost import CatBoostClassifier
import pandas as pd
from main import data, feature_class_correlation, class_boxplot, cap_diameter_histplot
from main import feature_mean_cap_diameter, class_ranged_by_stem_height, cap_diams_stem_heights
from main import stem_height_scatterplot, stem_width_boxplot
import gradio as gr



# Автор: Ро Александр
def fetch_parameters():
    """
    Загружает параметры из JSON-файла и форматирует их в список словарей.

    Returns:
        list: Список параметров, каждый из которых представлен словарём
              с ключами: 'name', 'type', 'values', 'image', 'prerequisites'.
    """
    with open("./resources/parameters.json", "r", encoding="utf-8") as file:
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


# Автор: Шмелев Антон
def create_component(param):
    """
    Создаёт UI-компонент Gradio на основе типа параметра.

    Args:
        param (dict): Словарь параметра с ключами 'name', 'type', 'values', 'image'.

    Returns:
        tuple: Кортеж из изображения (gr.Image или None) и соответствующего компонента Gradio.

    Raises:
        KeyError: Если указан неизвестный тип компонента.
    """
    image = gr.Image(param["image"], interactive=False, show_label=False, height=100) \
        if param["image"] is not None else None

    kwargs = {"label": " ".join(param["name"].split("-")).capitalize()} # noqa
    if param["type"] == "text":
        return (image, gr.Textbox(**kwargs)) \
            if param["values"] is None else (image, gr.Radio(param["values"], **kwargs))

    if param["type"] == "number":
        return image, gr.Number(**kwargs)

    if param["type"] == "list":
        return (image, gr.Textbox(**kwargs)) \
            if param["values"] is None else (image, gr.CheckboxGroup(param["values"], **kwargs))

    if param["type"] == "bool":
        return image, gr.Checkbox(**kwargs)

    raise KeyError(f"Invalid type {param['type']}")


# Автор: Ро Александр
def setup_visibility(components, connections):
    """
    Настраивает динамическую видимость компонентов интерфейса на основе связей.

    Args:
        components (dict): Словарь компонентов, где ключ — имя параметра,
                           значение — кортеж (изображение, компонент).
        connections (list): Список связей вида (parent_name, [child_names]),
                            определяющих, какие компоненты должны появляться при выборе.
    """
    for lhs, rhs in connections:
        parent = components[lhs]
        child = list(map(lambda x: x, components[rhs]))

        for element in child:
            element.visible = False

        parent[1].change(
            lambda x, child=child: [
                gr.update(visible = x == "true") for _ in child],
            inputs=parent[1],
            outputs=child
        )

dct = {
        "cap-shape": {
            "possible_values": ["Колокольчатая","Коническая",
                                "Выпуклая", "Плоская", "С выступом",  "Вогнутая"]
        },
        "cap-surface": {
            "possible_values": ["Волокнистая",  "С бороздками",  "Чешуйчатая", "Гладкая"]
        },
        "cap-color": {
            "possible_values": ["Коричневый", "Охристый",
                                "Коричнево-оранжевый", "Серый","Зеленый", "Розовый",
                                "Фиолетовый", "Красный", "Белый",
                                "Желтый"]
        },
        "does-bruise-or-bleed": {
            "possible_values": ["Да", "Нет"]
        },
        "gill-attachment": {
            "possible_values": ["Приросшие", "Нисходящие (сползают по ножке вниз)",
                                "Свободные", "Приросшие к ножке зубцом"]
        },
        "gill-color": {
             "possible_values": ["Черный","Коричневый", "Желтовато-коричневый",
                                 "Шоколадный", "Серый","Зеленый", "Оранжевый" ,"Розовый",
                                 "Фиолетовый", "Красный", "Белый",
                                "Желтый"]
        },
        "stem-color": {
             "possible_values": ["Коричневый", "Охристый", "Коричнево-оранжевый",
                                 "Серый","Оранжевый", "Розовый",  "Красный", "Белый",
                                "Желтый"]
        },
        "has-ring": {
            "possible_values": ["true", "false"]
        },
        "ring-type": {
            "possible_values": ["Паутинистое", "Исчезающее", "Плоское",
                                "Крупное", "Отсутсвует", "Юбкообразное", "Раструбовидное",
                                "Кольцевая зона или след"],
        },
        "habitat": {
            "possible_values": ["Трава", "Лиственная подстилка", "Луга",
                                "Тропинки", "Город", "Свалки", "Леса"]
        },
        "season": {
            "possible_values": ["Лето", "Осень", "Зима", "Весна"]
        }
    }

letters_map = {
            'cap-shape': ['b', 'c', 'x', 'f', 'k', 's'],
            'cap-surface': ['f', 'g', 'y', 's'],
            'cap-color': ['n', 'b', 'c', 'g', 'r', 'p', 'u', 'e', 'w', 'y'],
            'does-bruise-or-bleed': ['t', 'f'],
            'gill-attachment': ['a', 'd', 'f', 'n'],
            'gill-color': ['k', 'n', 'b', 'h', 'g', 'r', 'o', 'p', 'u', 'e', 'w', 'y'],
            'stem-color': ['n', 'b', 'c', 'g', 'o', 'p', 'e', 'w', 'y'],
            'has-ring': ['t', 'f'],
            'ring-type': ['c', 'e', 'f', 'l', 'n', 'p', 's', 'z'],
            'habitat': ['g', 'l', 'm', 'p', 'u', 'w', 'd'],
            'season': ['a', 'w', 'u', 's']
        }
# Автор: Ро Александр
def get_letter_by_value(feature: str, value) -> str | int | None:
    """
            Возвращает буквенное обозначение значения параметра
            на основе заданных справочников.

            Args:
                feature (str): Название параметра.
                value (str | int): Значение параметра.

            Returns:
                str | int | None: Буквенный код параметра, если найден,
                                  целое число, если value — int,
                                  или None, если сопоставление невозможно.
            """
    if isinstance(value, int):
        return value

    if feature not in dct or feature not in letters_map:
        return None

    possible_values = dct[feature]["possible_values"]
    letters = letters_map[feature]

    if value not in possible_values:
        return None

    index = possible_values.index(value)
    if index >= len(letters):
        return None

    return letters[index]

# Автор: Ро Александр
def feature_class_corr(feature):
    """
        Вычисляет корреляцию между указанным признаком и целевым классом,
        сохраняет результат в CSV-файл и возвращает его.

        Args:
            feature (str): Название признака для расчёта корреляции.

        Returns:
            pd.DataFrame: Таблица с рассчитанной корреляцией.
        """

    while None is feature:
        raise gr.Error("Выбери все параметры для гриба")

    result = feature_class_correlation(data, feature)
    result.to_csv('./graphics/feature_class_corr.csv')
    return result

# Автор: Андреев Алексанр
def feature_mean_cap_diam(*args):
    """
        Вычисляет средний диаметр шляпки гриба для комбинации трёх заданных параметров,
        сохраняет результат в CSV-файл и возвращает его.

        Args:
            *args: Кортеж из трёх строк — значений признаков.

        Returns:
            pd.DataFrame: Таблица со средними значениями диаметров.
        """

    while None in args[0] or len(args[0]) < 3:
        raise gr.Error("Выбери все параметры для гриба")

    feature_1, feature_2, feature_3 = args[0]

    result = feature_mean_cap_diameter(data, feature_1, feature_2, feature_3)
    result.to_csv('./graphics/feature_mean_cap_diam.csv')
    return result.to_html()

# Автор: Андреев Александр
def class_ranged_by_height(*args):
    """
       Группирует грибы по диапазону высоты ножки и сохраняет результат в CSV-файл.

       Args:
           *args: Кортеж из двух значений — начала и конца диапазона.

       Returns:
           pd.DataFrame: Таблица с распределением по диапазону высот.
       """

    while None in args or len(args) < 2:
        raise gr.Error("Выбери все параметры для гриба")

    begin, end = args
    result = class_ranged_by_stem_height(data, begin, end).to_frame().reset_index()
    result.to_csv('./graphics/class_ranged_by_height.csv')
    return result

# Автор: Чапайкин Арсений
def cap_diams_heights(*args):
    """
        Группирует данные по диапазону диаметров шляпки и сезону,
        возвращает результаты в виде таблицы и сохраняет в CSV.

        Args:
            *args: Кортеж из трёх значений — начала диапазона, конца диапазона и сезона.

        Returns:
            pd.DataFrame: Таблица с распределением по диапазонам диаметров и сезонам.
        """

    while None in args or len(args) < 3:
        raise gr.Error("Выбери все параметры для гриба")

    width_begin, width_end, season = args
    result = cap_diams_stem_heights(data, width_begin, width_end, season).reset_index()
    result.to_csv('./graphics/cap_diams_heights.csv')
    return result

# Автор: Чапайкин Арсений
def boxplot(numeric_feature):
    """
        Строит boxplot для числового признака по классам грибов
        и сохраняет изображение.

        Args:
            numeric_feature (str): Название числового признака.

        Returns:
            str: Путь к сохранённому изображению.
        """

    while None is numeric_feature:
        raise gr.Error("Выбери все параметры для гриба")

    class_boxplot(data, numeric_feature)
    return "./graphics/class_boxplot.png"

# Автор: Чапайкин Арсений
def cap_diameter_hist(numeric_feature):
    """
       Строит гистограмму распределения диаметров шляпок грибов
       и сохраняет изображение.

       Args:
           numeric_feature (str): Название числового признака.

       Returns:
           str: Путь к сохранённому изображению.
       """

    while None is numeric_feature:
        raise gr.Error("Выбери все параметры для гриба")

    cap_diameter_histplot(data, numeric_feature)
    return "./graphics/cap_diameter_histplot.png"

# Автор: Шмелев Антон
def stem_scatterplot(*args):
    """
        Строит scatterplot между числовым признаком и категориальным,
        сохраняет изображение.

        Args:
            *args: Кортеж из двух значений — числового и категориального признака.

        Returns:
            str: Путь к сохранённому изображению.
        """

    while None in args or len(args) < 2:
        raise gr.Error("Выбери все параметры для гриба")

    numeric_feature, cat_feature = args
    stem_height_scatterplot(data, numeric_feature, cat_feature)
    return "./graphics/stem_height_scatterplot.png"

# Автор: Шмелев Антон
def stem_boxplot(feature):
    """
        Строит boxplot для ширины ножки гриба по классам и сохраняет изображение.

        Args:
            feature (str): Название признака.

        Returns:
            str: Путь к сохранённому изображению.
        """

    while None is feature:
        raise gr.Error("Выбери все параметры для гриба")

    stem_width_boxplot(data, feature)
    return "./graphics/stem_width_boxplot.png"


# Авторы: Чапайкин Арсений, Андреев Александр
def head():
    """
    Главная функция отображения интерфейса
    """

    with gr.Blocks() as demo:
        components = {}
        connections = []
        tmp = fetch_parameters()

        for param in tmp[:-12]:
            with gr.Group():
                components[param["name"]] = create_component(param)
                if param["prerequisites"]:
                    connections.extend((parent, param["name"])
                                       for parent in param["prerequisites"])

        setup_visibility(components, connections)

        def debug(*args):
            """
                Отладочная функция, содержащая данные о возможных значениях параметров грибов
                и их сопоставление с буквенными кодами.
        
                Args:
                    *args: Переменное количество аргументов, не используется в теле функции.
            """
            model = CatBoostClassifier()
            model.load_model("./notes/classifier.cbm")
            preprocessor = joblib.load("./scripts/my_preprocessor.pkl")
            param = list(components.keys())
            pairs = zip(param, args)
            input_dict = {name: get_letter_by_value(name, value) for name, value in pairs}
            values = list(input_dict.values())
            values = values[:8] + values[9:]
            while None in values:
                raise gr.Error("Выбери все параметры для гриба")
            data_dict = pd.DataFrame(input_dict, index=[0])
            pd.set_option('display.max_columns', None)
            x_prediction = preprocessor.transform(data_dict)
            prediction = model.predict(x_prediction)
            return str(prediction[0])
        gr.Button("Submit") .click(# pylint: disable=no-member
            fn=debug, # noqa
            inputs=[comp[1] for comp in components.values()], # noqa
            outputs=gr.Textbox(label="Result")) # noqa


        tmp_lst = {tmp[-12]["name"]: create_component(tmp[-12])}


        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=feature_class_corr,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.DataFrame(headers=['1 уровень', '2 уровень', 'Значения'])
        )


        tmp_lst = {tmp[-11]["name"]: create_component(tmp[-11])}

        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=feature_mean_cap_diam,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.HTML()
        )

        tmp_lst = {tmp[-10]["name"]: create_component(tmp[-10]),
                   tmp[-9]["name"]: create_component(tmp[-9])}


        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=class_ranged_by_height,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.DataFrame()
        )

        tmp_lst = {tmp[-8]["name"]: create_component(tmp[-8]),
                   tmp[-7]["name"]: create_component(tmp[-7]),
                   tmp[-6]["name"]: create_component(tmp[-6])}

        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=cap_diams_heights,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.DataFrame()
        )

        tmp_lst = {tmp[-5]["name"]: create_component(tmp[-5])}

        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=boxplot,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.Image()
        )

        cap_diameter = tmp[-4]["name"]
        tmp_lst = {cap_diameter: create_component(tmp[-4])}



        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=cap_diameter_hist,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.Image()
        )
        tmp_lst = {tmp[-3]["name"]: create_component(tmp[-3]),
                   tmp[-2]["name"]: create_component(tmp[-2])}




        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=stem_scatterplot,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.Image()
        )


        tmp_lst = {tmp[-1]["name"]: create_component(tmp[-1])}



        btn = gr.Button("Submit")
        btn.click(# pylint: disable=no-member
            fn=stem_boxplot,
            inputs=[comp[1] for comp in tmp_lst.values()],
            outputs=gr.Image()
        )


    demo.launch()


if __name__ == "__main__":
    head()
