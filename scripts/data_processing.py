from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from scipy.sparse import csr_matrix, hstack


class DataPreprocessor(TransformerMixin, BaseEstimator):
	def __init__(self, needed_columns=None, valid_values=None, target_column=None):
		self.scaler = StandardScaler()
		self.ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=True)
		self.needed_columns = needed_columns
		self.valid_values = valid_values
		self.categorical_columns = []
		self.continuous_columns = []
		self.target_column = target_column

	def fit(self, X):
		data = X.copy()

		if self.needed_columns is not None:
			data = data[self.needed_columns]

		if self.target_column in data.columns:
			data = data.drop(columns=[self.target_column])

		self.continuous_columns = [col for col in data.columns if data[col].dtype in ('float64', 'int64') and col != self.target_column]
		self.categorical_columns = [col for col in data.columns if data[col].dtype not in ('float64', 'int64') and col != self.target_column]

		if self.valid_values is not None:
			for col in self.categorical_columns:
				data = data[data[col].isin(self.valid_values[col])]

		self.ohe.fit(data[self.categorical_columns])
		self.scaler.fit(data[self.continuous_columns])

		return self

	def transform(self, X):
		data = X.copy()

		targetExists = self.target_column in data.columns

		if self.needed_columns is not None:
			# Проверим, чтобы все нужные колонки были в датафрейме
			missing_cols = set(self.needed_columns) - set(data.columns)
			if missing_cols:
				raise ValueError(f"Missing columns in input data: {missing_cols}")
			data = data[self.needed_columns + [self.target_column] if targetExists else self.needed_columns]

		# Заполнение пропусков для категориальных переменных
		for col in self.categorical_columns:
			if col in data.columns:
				mode_val = data[col].mode(dropna=True)
				if not mode_val.empty:
					data.loc[:, col] = data[col].fillna(mode_val[0])
				else:
					data.loc[:, col] = data[col].fillna("unknown")

		# Заполнение пропусков для числовых переменных
		for col in self.continuous_columns:
			if col in data.columns:
				data.loc[:, col] = data[col].fillna(data[col].median())

		if self.valid_values is not None:
			for col in self.categorical_columns:
				if col in data.columns:
					if col == "ring-type":
						mask_with_ring = (data["has-ring"] == 't')
						mask_valid_ring = data[col].isin(self.valid_values[col])
						data = data[~(mask_with_ring & ~mask_valid_ring)]
					else:
						data = data[data[col].isin(self.valid_values[col])]

		if data.shape[0] == 0:
			raise ValueError("No samples left after filtering by valid_values. Check your input data.")

		if targetExists:
			y = data[self.target_column]
			data = data.drop(columns=[self.target_column])

		# Проверяем, что все continuous_columns есть в data
		missing_cont_cols = set(self.continuous_columns) - set(data.columns)
		if missing_cont_cols:
			raise ValueError(f"Missing continuous columns in input data: {missing_cont_cols}")

		# Проверяем, что все categorical_columns есть в data
		missing_cat_cols = set(self.categorical_columns) - set(data.columns)
		if missing_cat_cols:
			raise ValueError(f"Missing categorical columns in input data: {missing_cat_cols}")

		# Если всё ок — трансформируем
		data1 = self.scaler.transform(data[self.continuous_columns])
		data2 = self.ohe.transform(data[self.categorical_columns])

		X_transformed = hstack([csr_matrix(data1), data2])

		return (X_transformed, y) if targetExists else X_transformed
