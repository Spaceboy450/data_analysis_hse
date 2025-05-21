# -*- coding: utf-8 -*-
"""
Python project. Binary classification of mushrooms.

Performed by: Andreev Alexander, Chapaykin Arseniy, Ro Alexander, Shmelev Anton 
"""

import pandas as pd
# import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ********************************************
# ********** Предобработка данных ************
# ********************************************


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
        # variable_name = name.lower().replace('-', '_') + '_guide'
        # exec(f'{variable_name} = file.parse(name)')
        # exec(f'{variable_name}.to_pickle("./work/data/{name}.pick")')
        guide_data = file.parse(guide_name)
        guide_data.to_pickle(f"{path}/{guide_name}.pick")
        result[guide_name] = guide_data.copy()
    return result

file_path = ('./data')

guides = configure_guides(file_path)

# Creating dictionary with valid values of each feature to filter invalid rows of df
valid_values = {}
for name, guide in guides.items():
    valid_values[name] = guide.loc[:, name].values
# print(valid_values)

# Reading data from CSV
data = pd.read_csv('./data/dataset.csv')


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
    return dataframe.groupby(feature)['class'].value_counts()


print('Корреляция значений конкретного категориального признака и целевого класса.')
while True:
    temp_feature = input('Введите название признака: ')
    if temp_feature in cat_columns:
        break
    print('Не найдено соответствующего категориального признака')
print(feature_class_correlation(data, 'cap-shape'))


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


print('Сводная таблица со средним диаметром шляпки гриба по трём признакам')
while True:
    temp_feature_1, temp_feature_2, temp_feature_3 = input(
        'Введите названия трёх категориальных признаков через пробел: '
    ).split()[:3]
    if (temp_feature_1 in cat_columns
        and temp_feature_2 in cat_columns
            and temp_feature_3 in cat_columns):
        break
    print('Не найдено соответствующих категориальных признаков')
print(feature_mean_cap_diameter(data,
                                temp_feature_1,
                                temp_feature_2,
                                temp_feature_3
                                ))


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


print('Классы грибов, имеющих высоту ножки из заданного диапазона')
l, r = map(int, input(
    'Введите нижнюю и верхнюю границы диапазона через пробел: ').split())
print(class_ranged_by_stem_height(data, l, r))


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


print('Значения диаметра шляпки и высоты ножки грибов,'
      'имеющих заданный сезон произрастания и'
      'ширина ножки которых лежит в заданном диапазоне')
while True:
    l, r = map(int, input(
        'Введите нижнюю и верхнюю границы диапазона через пробел: ').split())
    s = input('Введите сезон: ')
    if s in ['a', 'w', 'u', 's']:
        break
print(cap_diams_stem_heights(data, l, r, s))

# ******************************************
# ********** Графические отчёты ************
# ******************************************


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
    return sns.boxplot(data=dataframe, x='class', y=numeric_feature, hue='class', showfliers=False)


print('Ящик с усами для числового признака, сгруппированного по классам грибов')
while True:
    temp_feature = input('Введите числовой признак: ')
    if temp_feature in num_columns:
        break
    print('Не найдено соответствующего числового признака')
ax = class_boxplot(data, temp_feature)
plt.show()


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
    return sns.histplot(data=dataframe, x='cap-diameter', hue=hue, binrange=(0, 17))


print('Гистограмма распределения диаметров шляпки грибов с разделением по категориальному признаку')
while True:
    temp_feature = input('Введите категориальный признак: ')
    if temp_feature in cat_columns:
        break
    print('Не найдено соответствующего категориального признака')
ax = cap_diameter_histplot(data, temp_feature)
plt.show()


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
    return sns.scatterplot(data=dataframe, x="stem-height", y=numeric_feature, hue=hue)


print('Точечный график зависимости между высотой ножки гриба'
      'и заданным числовым признаком с разделением'
      'по некоторому категориальному признаку')
while True:
    temp_feature_1 = input('Введите числовой признак: ')
    temp_feature_2 = input('Введите категориальный признак: ')
    if temp_feature_1 in num_columns and temp_feature_2 in cat_columns:
        break
    print('Не найден один или несколько из введенных признаков')
ax = stem_height_scatterplot(data, temp_feature_1, temp_feature_2)
plt.show()


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
    return sns.boxplot(data=dataframe, x='cap-diameter', y=object_feature, showfliers=False)


print('Boxplot (ящик с усами) для диаметра шляпки,'
      'сгруппированного по заданному категориальному признаку')
while True:
    temp_feature = input('Введите категориальный признак: ')
    if temp_feature in cat_columns:
        break
    print('Не найдено соответствующего категориального признака')
ax = stem_width_boxplot(data, temp_feature)
plt.show()
