# -*- coding: utf-8 -*-
"""
Python project. Binary classification of mushrooms.

Performed by: Shmelev Anton, Ro Alexander, Chapaykin Arseniy, Andreev Alexander 
"""

import pandas as pd
import numpy as np

def configure_guides(path):
	"""
	Configurates guides from MS Excel file

	Args:
		path (str): Path to data

	Returns:
		Dict[str, pd.DataFrame]: Dictionary with:
			- key (str): Feature name
			- value (pd.DataFrame): Corresponding guide
	"""
	guides = dict()
	file = pd.ExcelFile(f'{path}/store.xlsx')

	for name in file.sheet_names[1:]:
		# variable_name = name.lower().replace('-', '_') + '_guide'
		# exec(f'{variable_name} = file.parse(name)')
		# exec(f'{variable_name}.to_pickle("./work/data/{name}.pick")')
		
		data = file.parse(name)
		data.to_pickle(f"{path}/{name}.pick")
		guides[name] = data.copy() 

	return guides

guides = configure_guides('../data')

# Creating dictionary with valid values of each feature to filter invalid rows of df
valid_values = dict()
for name, guide in guides.items():
	 valid_values[name] = guide.loc[:, name].values
# print(valid_values)

# Reading data from CSV
data = pd.read_csv('../data/dataset.csv')

def count_na_percentage(feature):
	"""
	Counts percentage of NaN values by feature name

	Args:
		feature (str): Feature name

	Returns:
		percentage (int): Percent of NaN values
	"""
	cnt_nulls = sum(data[feature].isna())
	n_rows = data.shape[0]
	percentage = round(cnt_nulls / n_rows * 100)
	return percentage

# Creating dictionary with percentages of NaN for each feature
na_percentages = dict()
for col in data.columns:
	na_percentages[col] = count_na_percentage(col)

# Array of columns that have less than 50% of NaNs
needed_columns = [key for key in data.columns if na_percentages[key] < 50 and key != 'id']
print(needed_columns)

# Selecting only interesting columns
data = data[needed_columns]
print(data)

# Finding categorical columns
cat_columns = [key for key in data.columns if data[key].dtype not in ('int64', 'float64')]

# Filling NaNs with mode and removing rows with invalid values
for col in cat_columns:
	data[col] = data[col].fillna(data[col].mode()[0])
	data = data[data[col].isin(valid_values[col])]

# Correlation of class by given feature
def feature_class_correlation(df, feature):
    return df.groupby(feature)['class'].value_counts()

# Pivot-table by three picked features
def feature_mean_cap_diameter(df, feature_1, feature_2, feature_3):
    return pd.pivot_table(df, values='cap-diameter', index=[feature_1, feature_2], columns=[feature_3], aggfunc="mean")

# Class ranged by picked range of stem-height
def class_ranged_by_stem_height(df, begin, end):
    df_picked = df[(df['stem-height'] >= begin) & (df['stem-height'] <= end)]
    return df_picked['class']

# Cap-diameters and stem-heights by stem-width and season
def cap_diams_stem_heights(df, width_begin, width_end, season):
    df_clean = df[(df['stem-width']>=width_begin) & (df['stem-width']<=width_end) & (df['season']==season)]
    return df_clean[['cap-diameter', 'stem-height']]

print(feature_class_correlation(data, 'cap-shape'))