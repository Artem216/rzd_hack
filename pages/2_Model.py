import data_preprossesing as dp 
import pandas as pd
import streamlit as st
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_squared_error, r2_score

path_data_rdy = './data/data_rdy.xlsx'
data = pd.read_excel(path_data_rdy)

col1, col2 = st.columns(2)
with col1:
    lag = st.slider('Выберите количество дней для предсказания', min_value=1, max_value=14, value=5, step=1)

data_cat = dp.func_for_catboost(data, lag)
data_cat = dp.get_new_rating(data_cat)

data_cat['grade'] = data_cat.groupby('Наименование полигона')['grade'].shift(-lag)
data_cat = data_cat.dropna(subset=['grade'])
data_cat = data_cat.sort_values(by='Дата')

train_size = int(len(data_cat) * 0.8)
train_df = data_cat.iloc[:train_size]
test_df = data_cat.iloc[train_size:]


X_train = train_df.drop(columns=['grade', 'Наименование полигона',	'Краткое наименование',	'Полигон',	'Наименование структурного подразделения', 'Rating 2.0'])
y_train = train_df['grade']
X_test = test_df.drop(columns=['grade', 'Наименование полигона',	'Краткое наименование',	'Полигон',	'Наименование структурного подразделения', 'Rating 2.0'])
y_test = test_df['grade']
cat_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

model = CatBoostRegressor(allow_writing_files=False,

                           iterations=1000, 
                          learning_rate=0.004, 
                          depth=4, 
                          eval_metric='RMSE', 
                          random_seed=42)

train_pool = Pool(X_train, y_train, cat_features=cat_features)

if st.button('model'):
    model_fit_result = model.fit(train_pool, verbose=100)
    st.write(model.get_params())
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    st.write(f"MSE на тесте: {mse}")
    st.write(f"R2 на тесте: {r2}")