# -*- coding: utf-8 -*-
"""
Python project. Binary classification of mushrooms.

Performed by: Andreev Alexander, Chapaykin Arseniy, Ro Alexander, Shmelev Anton 
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ********************************************
# ********** Предобработка данных ************
# ********************************************


# Автор: Шмелев Антон
def configure_guides(path):
    """
        Конфигурирует справочники из MS Excel файла, также записывает их в pickle-файлы.

        Args:
                path (str): Путь к Excel файлу и к тому, куда будут сохранены pickle-файлы

        Returns:
                Dict[str, pd.DataFrame]: Словарь, включающий в себя:
                        - key (str): Название признака
                        - value (pd.DataFrame): Соответствующий справочник
        """
    result = {}

    file = pd.ExcelFile(f'{path}/store.xlsx')
    for guide_name in file.sheet_names[1:]:
        guide_data = file.parse(guide_name)
        guide_data.to_pickle(f"{path}/{guide_name}.pick")
        result[guide_name] = guide_data.copy()
    return result

FILE_PATH = './data'

guides = configure_guides(FILE_PATH)

# Creating dictionary with valid values of each feature to filter invalid rows of df
valid_values = {}
for name, guide in guides.items():
    valid_values[name] = guide.loc[:, name].values
# print(valid_values)

# Reading data from CSV
data = pd.read_csv('./data/dataset.csv')


# Автор: Чапайкин Арсений
def count_na_percentage(dataframe, feature):
    """
        Подсчитывает процент NaN значений от общего числа в колонке feature датафрейма df.

        Args:
                dataframe (pd.DataFrame): Рассматриваемый датафрейм
                feature (str): Название признака

        Returns:
                int: Процент NaN значений от общего числа
        """
    cnt_nulls = sum(dataframe[feature].isna())
    n_rows = dataframe.shape[0]
    percentage = round(cnt_nulls / n_rows * 100)
    return percentage


# Creating dictionary with percentages of NaN for each feature
na_percentages = {}
for col in data.columns:
    na_percentages[col] = count_na_percentage(data, col)

# Array of columns that have less than 50% of NaNs
needed_columns = [
    key for key in data.columns if na_percentages[key] < 50 and key != 'id']
# print(needed_columns)

# Selecting only interesting columns
data = data[needed_columns]
# print(data.sample(5))

# Finding categorical columns
cat_columns = [
    key for key in data.columns if data[key].dtype not in ('int64', 'float64')]
num_columns = [key for key in data.columns if key not in cat_columns]

# Filling NaNs with mode and removing rows with invalid values
for col in cat_columns:
    data[col] = data[col].fillna(data[col].mode()[0])
    data = data[data[col].isin(valid_values[col])]


# ****************************************
# ********** Текстовые отчёты ************
# ****************************************


# Автор: Ро Александр
def feature_class_correlation(dataframe, feature):
    """
        Считает количество встречаемых значений указанного
    признака в разбивке по классам (poisonous/edible).

        Args:
                dataframe (pd.DataFrame): Рассматриваемый датафрейм
                feature (str): Название признака

        Returns:
                pd.Series: Series с мультииндексом в котором:
                        - 1-й уровень: уникальные значения признака
                        - 2-й уровень: метки классов (e - съедобный, p - ядовитый)
                        - значения: количество соответствующих наблюдений
    """
    return dataframe.groupby(feature)['class'].value_counts().reset_index(name='count')


# Автор: Ро Александр
def feature_mean_cap_diameter(dataframe, feature_1, feature_2, feature_3):
    """
        Строит сводную таблицу со средним диаметром шляпки
    гриба по комбинациям трёх выбранных категориальных признаков.

        Args:
                dataframe (pd.DataFrame): Рассматриваемый датафрейм
                feature_1 (str): Название первого признака
                feature_2 (str): Название второго признака
                feature_3 (str): Название третьего признака

        Returns:
                pd.DataFrame: Сводная таблица по исходным данным
        """
    return pd.pivot_table(
        dataframe,
        values='cap-diameter',
        index=[feature_1, feature_2],
        columns=[feature_3],
        aggfunc="mean"
    )


# Автор: Ро Александр
def class_ranged_by_stem_height(dataframe, begin, end):
    """
        Отбирает грибы у которых значение высоты
    ножки лежит в заданном диапазоне и возвращает серию с их классами.

        Args:
                dataframe (pd.DataFrame): Рассматриваемый датафрейм
                begin (int): Нижняя граница рассматриваемого диапазона
                end (int): Верхняя граница рассматриваемого диапазона

        Returns:
                pd.Series: Серия с классами грибов, удовлетворяющих условию
        """
    df_picked = dataframe[(dataframe['stem-height'] >= begin)
                          & (dataframe['stem-height'] <= end)]
    return df_picked['class']


# Автор: Андреев Александр
def cap_diams_stem_heights(dataframe, width_begin, width_end, season):
    """
        Отбирает грибы по конкретному сезону произрастания у которых
    значение ширины ножки лежит в заданном диапазоне
    и возвращает серию с их диаметрами шляпки и высотами ножки.

        Args:
                dataframe (pd.DataFrame): Рассматриваемый датафрейм
                width_begin (int): Нижняя граница рассматриваемого диапазона
                width_end (int): Верхняя граница рассматриваемого диапазона
                season (str): Сезон в формате:
                    - a - осень
                    - w - зима
                    - u - лето
                    - s - весна

        Returns:
                pd.Series: Серия с диаметрами шляпки и
        высотами ножки грибов, удовлетворяющих условию
        """
    df_clean = dataframe[
        (dataframe['stem-width'] >= width_begin)
        & (dataframe['stem-width'] <= width_end)
        & (dataframe['season'] == season)
    ]
    return df_clean[['cap-diameter', 'stem-height']]


# ******************************************
# ********** Графические отчёты ************
# ******************************************


# Автор: Андреев Александр
def class_boxplot(dataframe, numeric_feature):
    """
    Строит boxplot (ящик с усами) для числового признака,
    сгруппированного по классам грибов (poisonous/edible).

    Args:
        dataframe (pd.DataFrame): Рассматриваемый датафрейм
        numeric_feature (str): Название признака

    Returns:
        matplotlib.axes.Axes: Объект Axes с построенным boxplot
    """
    plot = sns.boxplot(data=dataframe, x='class', y=numeric_feature, hue='class', showfliers=False)
    fig = plot.get_figure()
    fig.savefig("./graphics/class_boxplot.png")
    plot.cla()


# Автор: Андреев Александр
def cap_diameter_histplot(dataframe, hue):
    """
    Строит гистограмму распределения диаметров шляпки
    грибов с разделением по категориальному признаку.

    Args:
        dataframe (pd.DataFrame): Рассматриваемый датафрейм
        hue (str): Название категориального признака

    Returns:
        matplotlib.axes.Axes: Объект Axes с построенной гистограммой
    """
    plot = sns.histplot(data=dataframe, x='cap-diameter', hue=hue, binrange=(0, 17))
    fig = plot.get_figure()
    fig.savefig("./graphics/cap_diameter_histplot.png")
    plot.cla()


# Автор: Чапайкин Арсений
def stem_height_scatterplot(dataframe, numeric_feature, hue):
    """
    Строит точечный график зависимости между высотой ножки
    гриба и заданным числовым признаком с разделением по некоторому категориальному признаку.

    Args:
        dataframe (pd.DataFrame): Рассматриваемый датафрейм
        numeric_feature (str): Название числового признака
        hue (str): Название категориального признака

    Returns:
        matplotlib.axes.Axes: Объект Axes с построенным точечным графиком
    """
    plot = sns.scatterplot(data=dataframe, x="stem-height", y=numeric_feature, hue=hue)
    fig = plot.get_figure()
    fig.savefig("./graphics/stem_height_scatterplot.png")
    plot.cla()


# Автор: Чапайкин Арсений
def stem_width_boxplot(dataframe, object_feature):
    """
    Строит boxplot (ящик с усами) для диаметра шляпки,
    сгруппированного по заданному категориальному признаку.

    Args:
        dataframe (pd.DataFrame): Рассматриваемый датафрейм
        object_feature (str): Название категориального признака

    Returns:
        matplotlib.axes.Axes: Объект Axes с построенным boxplot
    """
    plot =  sns.boxplot(data=dataframe, x='cap-diameter', y=object_feature, showfliers=False)
    fig = plot.get_figure()
    fig.savefig("./graphics/stem_width_boxplot.png")
    plot.cla()


