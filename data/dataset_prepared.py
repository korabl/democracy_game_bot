import numpy as np
import pandas as pd
pd.set_option('display.float_format', '{:.2f}'.format)
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data_csv/dataset.csv")
df.drop(columns=["Median Age medium"], inplace=True)
df.drop(columns=["Code"], inplace=True)
df = df[df["Year"] >= 1900].copy()

# Выведем количество пропусков по каждому столбцу
print(df.isnull().sum().sort_values(ascending=False))

# Чистим данные
num_cols = df.select_dtypes(include=['float64', 'int64']).columns
df[num_cols] = df[num_cols].fillna(df[num_cols].median())

cat_cols = df.select_dtypes(include='object').columns
df[cat_cols] = df[cat_cols].fillna("Unknown")

threshold = 0.1 * len(df)
df = df.loc[:, df.notnull().sum() > threshold]


### Приступаем к обучению модели регрессии данных
# Убедимся, что данные отсортированы по стране и по году
df = df.sort_values(["Entity", "Year"]).reset_index(drop=True)

# Выберем только числовые столбцы (float/int), исключая Year,
# чтобы не считать дельту самого года:
numeric_cols = [
    col for col in df.columns
    if df[col].dtype in (float, int) and col not in ["Year"]
]

# Для каждого числового столбца считаем дельту
# groupby('Country') нужен, если у вас несколько стран,
# чтобы разница считалась отдельно для каждой страны
for col in numeric_cols:
    df[f"{col}_delta"] = df.groupby("Entity")[col].diff()

# Теперь в df появятся новые столбцы с суффиксом "_delta"
# В каждой группе (стране) первая строка будет NaN, так как нет предыдущего года

# Сохраним чистый датасет
df.to_csv("data_csv/dataset_clear.csv", index=False)

# Обучаем модель регресии
# 1. Определяем списки столбцов
# Столбцы с дельтами – заканчиваются на "_delta"
delta_columns = [col for col in df.columns if col.endswith('_delta')]
# Основные метрики – числовые столбцы, кроме Entity, Year и столбцов с "_delta"
primary_columns = [col for col in df.columns
                   if (col not in ["Entity", "Year"]) and (not col.endswith('_delta'))]

# 2. Сортируем данные по стране и году
df = df.sort_values(["Entity", "Year"]).reset_index(drop=True)

# 3. Создаём колонки baseline: для каждой метрики baseline = значение из предыдущего года в группе по стране
for col in primary_columns:
    df["baseline_" + col] = df.groupby("Entity")[col].shift(1)

# 4. Отбираем строки, где baseline заполнены и все delta заполнены
baseline_columns = ["baseline_" + col for col in primary_columns]
df_train = df.dropna(subset=baseline_columns + delta_columns)

# 5. Формируем обучающие данные:
# Входной вектор X – объединение baseline и текущих дельт
X = df_train[baseline_columns + delta_columns].values   # размерность (n_samples, 66), если 33 метрики
# Целевая переменная y – абсолютные значения метрик текущего периода
y = df_train[primary_columns].values                    # размерность (n_samples, 33)

# 6. Нормализуем входные и целевые данные
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y)

# 7. Разбиваем данные на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.2, random_state=42)

# 8. Обучаем модель, например, RandomForestRegressor (многовыходовая регрессия)
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# Оцениваем модель на тестовой выборке (метрика R^2)
test_score = model.score(X_test, y_test)
print("Test score (R^2):", test_score)

# Проверяем модель на тестовом семпле
try:
    scaler_combined
except NameError:
    class IdentityScaler:
        def transform(self, X):
            return X
    scaler_combined = IdentityScaler()

try:
    scaler_delta
except NameError:
    class IdentityScaler:
        def transform(self, X):
            return X
        def inverse_transform(self, X):
            return X
    scaler_delta = IdentityScaler()

# --- Шаг 1. Задаем текущий контекст (baseline)
current_baseline = {
    "Civil liberties index": 0.8,
    "Taxes (% GDP)": 25.0,
    "GDP/capita, $": 35000,
    "Population": 50e6,
    "Average years of education": 12.5,
    "Meat, kg/year/capita": 30,
    "Deaths in ongoing conflicts": 0,
    "Child deaths per 100 live births": 3,
    "GDP": 1.2e12,
    "Inequality Index": 0.35,
    "Median Age estimates": 38,
    "Period life expectancy": 78,
    "Urban population": 0.7,
    "Rural population": 0.3,
    "Total number of emigrants": 0.5e6,
    "Healthcare expenditure (% GPD)": 8.5,
    "Energy used per capita": 2000,
    "Agricultural land (% of land area)": 40,
    "Prevalence of undernourishment": 5,
    "Share below $2.15 a day": 10,
    "GNI per capita": 30000,
    "GDP per person employed": 100000,
    "GDP growth observation": 2.0,
    "GDP growth forecasts": 2.5,
    "Government expenditure (% of GDP)": 20,
    "Government expenditure on education (% of GDP)": 5,
    "State capacity estimate": 0.6,
    "Functioning government": 0.7,
    "Political corruption index": 0.4,
    "Rule of Law index": 0.8,
    "Internet availability": 0.9,
    "Happiness & Life-satisfaction": 7.5,
    "Military expenditure (% of GDP)": 2.0
}

primary_columns = list(current_baseline.keys())
# delta_columns – имена метрик с добавлением суффикса "_delta"
delta_columns = [metric + "_delta" for metric in primary_columns]

# --- Шаг 2. Задаем вектор изменений (дельт), полученный от пользователя
user_delta = {
    "Taxes (% GDP)_delta": 10,              # Повышение налога на 10 п.п.
    "Average years of education_delta": -0.5  # Снижение среднего образования на 0.5 лет
    # Если изменений не указано, значение считается 0.
}
# Формируем полный вектор дельт – для метрик, для которых изменений не указано, подставляем 0.
delta_input = {col: user_delta.get(col, 0) for col in delta_columns}

# --- Шаг 3. Объединяем baseline и вектор изменений в один входной вектор
# Входной вектор состоит из двух частей: текущие абсолютные значения (baseline) и вектор изменений (дельт)
baseline_series = pd.Series(current_baseline)      # 33 признака
delta_series = pd.Series(delta_input)              # 33 признака
combined_input = pd.concat([baseline_series, delta_series])  # итоговый вектор: 66 признаков
input_df = pd.DataFrame([combined_input])

# --- Шаг 4. Масштабирование и инференс
# Приводим входной вектор к тому же масштабу, на котором обучалась модель.
input_scaled = scaler_combined.transform(input_df)

# model – это обученная ML-модель, которая принимает объединённый вектор (66 признаков)
# и предсказывает полный вектор изменений (дельт) для всех метрик.
predicted_delta_scaled = model.predict(input_scaled)
predicted_delta = scaler_delta.inverse_transform(predicted_delta_scaled)

# --- Шаг 5. Вычисляем финальный прогноз
# Для метрик, для которых пользователь указал изменения, используем их напрямую (baseline + user_delta)
# Для остальных метрик прибавляем к baseline то, что предсказала модель.
final_prediction = {}
for i, metric in enumerate(primary_columns):
    user_val = user_delta.get(metric + "_delta", 0)
    if user_val != 0:
        final_prediction[metric] = current_baseline[metric] + user_val
    else:
        final_prediction[metric] = current_baseline[metric] + predicted_delta[0][i]

# --- Шаг 6. Формируем сравнительную таблицу "Было – Стало"
comparison_df = pd.DataFrame({
    "Metric": primary_columns,
    "Baseline": [current_baseline[metric] for metric in primary_columns],
    "Predicted": [final_prediction[metric] for metric in primary_columns]
})
comparison_df["Difference"] = comparison_df["Predicted"] - comparison_df["Baseline"]
comparison_df["Difference (%)"] = 100 * (comparison_df["Predicted"] - comparison_df["Baseline"]) / comparison_df["Baseline"]

print("Сравнительная таблица 'Было – Стало':")
print(comparison_df.to_string(index=False))

# Сохраняем обученную модель
import joblib

# Сохраняем модель в файл trained_model.pkl
joblib.dump(model, "trained_model.pkl")

# Для сохранения масштабировщиков (если они есть), можно сохранить их аналогично:
joblib.dump(scaler_X, "scaler_X.pkl")
joblib.dump(scaler_y, "scaler_y.pkl")

print("Модель и скейлеры успешно сохранены.")