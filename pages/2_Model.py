import data_preprossesing as dp 
import pandas as pd
import streamlit as st
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_squared_error, r2_score
import os
import altair as alt
import plotly.graph_objs as go
import plotly.express as px

import streamlit_authenticator as stauth


import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Model", 
                    layout="wide")



with open('auth.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

name, authentication_status, username = authenticator.login()

if authentication_status:

   path_data_rdy = './data/data_rdy.xlsx'
data = pd.read_excel(path_data_rdy)

dict_poligon_park, dict_park_poligon = dp.get_dicts_poligon_park(data)
col1, col2, col3 = st.columns(3)
with col1:
    poligon = st.selectbox(
        "Выберите полигон",
        dp.get_list_poligon(data),
        index=None,
        placeholder="Выберите полигон...")

if poligon:
    with col2:
        park = st.selectbox(
            "Выберите подразделение",
            dict_poligon_park.get(poligon),
            index=None,
            placeholder="Выберите подразделение...")

col1, col2 = st.columns(2)
with col1:
    lag = st.slider('Выберите количество дней для предсказания', min_value=1, max_value=14, value=5, step=1)

col1, col2, col3 = st.columns(3)
if col1.button('Рассчитать'):
    if not isinstance(poligon, str) or not isinstance(park, str) or not isinstance(lag, int):
        st.write('Заполните все поля')
    else:
        data_cat = dp.func_for_catboost(data, lag)
        data_cat = dp.get_new_rating(data_cat)

        cols = ['Наименование полигона', 'Наименование структурного подразделения']
        data_cat['grade'] = data_cat.groupby(cols)['grade'].shift(-lag)
        data_cat_fut = data_cat.groupby(cols).apply(lambda df: df[df['grade'].isna()][list(set(df.columns) - set(cols))]).reset_index().drop(columns='level_2')
        data_cat = data_cat.dropna(subset=['grade'])
        data_cat = data_cat.sort_values(by='Дата')

        train_df = data_cat.groupby(cols).apply(lambda df: df.iloc[:int(len(df) * 0.8), :][list(set(df.columns) - set(cols))]).reset_index().drop(columns='level_2')
        test_df = data_cat.groupby(cols).apply(lambda df: df.iloc[int(len(df) * 0.8):, :][list(set(df.columns) - set(cols))]).reset_index().drop(columns='level_2')

        X_train = train_df.drop(columns=['grade', 'Наименование полигона', 'Краткое наименование', 'Полигон', 'Наименование структурного подразделения', 'Rating 2.0'])
        y_train = train_df['grade']
        X_test = test_df.drop(columns=['grade', 'Наименование полигона', 'Краткое наименование', 'Полигон',	'Наименование структурного подразделения', 'Rating 2.0'])
        y_test = test_df['grade']
        X_fut = data_cat_fut.drop(columns=['grade', 'Наименование полигона', 'Краткое наименование', 'Полигон', 'Наименование структурного подразделения', 'Rating 2.0'])

        cat_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
        model = CatBoostRegressor(allow_writing_files=False ,iterations=1000, 
                                learning_rate=0.004, 
                                depth=4, 
                                eval_metric='RMSE', 
                                random_seed=42)

        train_pool = Pool(X_train, y_train, cat_features=cat_features)

        model_fit_result = model.fit(train_pool, verbose=False)
        y_test_pred = model.predict(X_test)
        y_fut_pred = model.predict(X_fut)

        with col1:
            st.header('Использование ТС')
            df_use = pd.DataFrame({'Использование': ['В целевой структуре парка', 'Прочие'],
                        'Количество машин': dp.get_info_use(data, poligon, park)})
            bars  = alt.Chart(df_use).mark_bar().encode(
            x=alt.X('Использование', axis=alt.Axis(labelAngle=0)),  # labelAngle=0 для горизонтальных меток
            y='Количество машин'
            ).properties(
                width=900  # Задаем ширину графика
            )

            text = bars.mark_text(
                align='center',
                baseline='bottom',
                dy=-5
            ).encode(
                text='Количество машин:Q'
            )

            chart = bars + text
            st.altair_chart(chart)

        st.header(f'Рейтинг')
        data_grade = dp.get_date_grade(data, poligon, park).rename(columns={'grade': 'Оценка подразделения',
                                                                            'mean_grade': 'Средняя оценка в полигоне'})
        
        data_cat_fut['grade'] = y_fut_pred
        train_df = train_df[(train_df['Наименование полигона'] == poligon) & 
                          (train_df['Наименование структурного подразделения'] == park)]
        test_df = test_df[(test_df['Наименование полигона'] == poligon) & 
                          (test_df['Наименование структурного подразделения'] == park)]
        data_cat_fut = data_cat_fut[(data_cat_fut['Наименование полигона'] == poligon) & 
                          (data_cat_fut['Наименование структурного подразделения'] == park)]
        
        data_cat_fut = pd.concat([test_df, data_cat_fut])
        fig = go.Figure()
        colors = ['blue', 'orange']
        for i, (df, name, color) in enumerate(zip([train_df, data_cat_fut], ['Известный Рейтинг', 'Предсказани Рейтинга'], colors)):
            fig.add_trace(go.Scatter(
                x=df['Дата'], 
                y=df['grade'],  # Замените 'grade' на соответствующий столбец для i-той линии
                mode='lines',
                line=dict(color=color),
                name=f'{name}'  # Добавьте подходящее имя для каждой линии
            ))


        fig.update_layout(
            title=f'Предсказание рейтинга на {lag} дней/ня',
            xaxis_title='Дата',
            yaxis_title='Рейтинг подразделения',
            legend=dict(x=0, y=1),
            width=800,
            height=400
        )

        # Отображение графика в Streamlit
        st.plotly_chart(fig)

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')