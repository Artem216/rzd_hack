import streamlit as st
import pandas as pd
import os
import data_preprossesing as dp 
import altair as alt
import plotly.graph_objs as go



import streamlit_authenticator as stauth


st.set_page_config(page_title="Dashboard", 
                   page_icon= "1️⃣",
                   layout="wide")

st.title("Предложения")
from dotenv import load_dotenv

load_dotenv()


MMDPR_LIST= ['test', 'test1']


import yaml
from yaml.loader import SafeLoader

# st.set_page_config(page_title="Dashboard", 
#                     page_icon= "1️⃣",
#                     layout="wide")


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
    authenticator.logout('Logout', 'main')
    
    
    path_data_rdy = './data/data_rdy.xlsx'
    data = pd.read_excel(path_data_rdy)

    if username in MMDPR_LIST:
            data = data[data['Наименование структурного подразделения'] == 'Московская механизированная дистанция погрузочно-разгрузочных рабо#']
            
    data_cat = dp.func_for_catboost(data, 1)

    data_filtered_poezdki = data[(data['Данные путевых листов, пробег'].notna()) & (data['Данные путевых листов, пробег'] != 0)]
    data_filtered_telematika = data[(data['Данные телематики, пробег'].notna()) & (data['Данные телематики, пробег'] != 0)]
    result_poezdki = data_filtered_poezdki.groupby(['Дата', 'Наименование структурного подразделения', 'Полигон'])['Данные путевых листов, пробег'].count().reset_index()
    result_telematika = data_filtered_telematika.groupby(['Дата', 'Наименование структурного подразделения', 'Полигон'])['Данные телематики, пробег'].count().reset_index()
    result = pd.merge(result_poezdki, result_telematika, on=['Дата', 'Наименование структурного подразделения', 'Полигон'], how='outer')
    type_counts = data.groupby(['Дата', 'Наименование структурного подразделения', 'Полигон', 'Тип закрепления']).size().unstack(fill_value=0).reset_index()
    result = pd.merge(result, type_counts, on=['Дата', 'Наименование структурного подразделения', 'Полигон'], how='outer')

    final_result = result.copy()

    result['Номера в целевой структуре парка'] = [[] for _ in range(len(result))] # в колонке  Тип закрепления имеют значение В целевой структуре парка, при этом  Данные телематики, пробег значение 0 или Null(отдыхали)
    result['Номерные знаки с пробегом'] = [[] for _ in range(len(result))] # в колонке Данные телематики, пробег	имеет значение не 0 и не Null
    result['Прочие номера'] = [[] for _ in range(len(result))] # Тип закрепления имеет значение Прочие
    result['Номера машин, которые целевые, но ездили, хотя не должны'] = [[] for _ in range(len(result))]

    for idx, row in result.iterrows():
        data_filtered = data[
            (data['Дата'] == row['Дата']) &
            (data['Наименование структурного подразделения'] == row['Наименование структурного подразделения']) &
            (data['Полигон'] == row['Полигон'])
        ]
        should_not_have_moved = data_filtered[
            (data_filtered['Тип закрепления'] == 'В целевой структуре парка') &
            ((data_filtered['Данные телематики, пробег'] != 0) & (~data_filtered['Данные телематики, пробег'].isna())) &
            ((data_filtered['Данные путевых листов, пробег'] == 0) | (data_filtered['Данные путевых листов, пробег'].isna()))
        ]['Номерной знак ТС'].tolist()

        in_target_structure = data_filtered[
            (data_filtered['Тип закрепления'] == 'В целевой структуре парка') &
            ((data_filtered['Данные телематики, пробег'] == 0) | (data_filtered['Данные телематики, пробег'].isna()))
        ]['Номерной знак ТС'].tolist()
        
        with_telematics_mileage = data_filtered[
            (data_filtered['Данные телематики, пробег'] != 0) & (~data_filtered['Данные телематики, пробег'].isna())
        ]['Номерной знак ТС'].tolist()
        
        others = data_filtered[
            (data_filtered['Тип закрепления'] == 'Прочие')
        ]['Номерной знак ТС'].tolist()
        
        result.at[idx, 'Номера машин, которые целевые, но ездили, хотя не должны'] = should_not_have_moved
        result.at[idx, 'Номера в целевой структуре парка'] = in_target_structure
        result.at[idx, 'Номерные знаки с пробегом'] = with_telematics_mileage
        result.at[idx, 'Прочие номера'] = others


    def give_chillusha(df_, start_date="2024-04-01", end_date="2024-04-30", group_by_column='Полигон', aggregate_column='Номера в целевой структуре парка'):
        df = df_.copy()
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df = df[(df['Дата'] >= start_date) & (df['Дата'] <= end_date)]
        poligon_car_relax = (
            df
            .explode(aggregate_column)
            .groupby(group_by_column)
            .agg({aggregate_column: list})
            .reset_index()
        )
        poligon_car_relax[aggregate_column] = poligon_car_relax[aggregate_column].map(lambda x: [i for i in x if isinstance(i, str)])
        poligon_car_relax['Количество машин в целевой структуре парка'] = poligon_car_relax[aggregate_column].map(lambda x: len(x))
        return poligon_car_relax

    dict_poligon_park, dict_park_poligon = dp.get_dicts_poligon_park(data)
    col1, col2, col3 = st.columns(3)
    poligon = col1.selectbox(
        "Выберите полигон",
        dp.get_list_poligon(data),
        index=None,
        placeholder="Выберите полигон...")

    user_date_input = col3.date_input(
    f"Значения для даты",
    value=(
        result['Дата'].min(),
        result['Дата'].max(),
    ))
    park = col2.selectbox(
        "Выберите подразделение",
        dict_poligon_park.get(poligon) if poligon else dp.get_list_park(data),
        index=None,
        placeholder="Выберите подразделение...")

    if col1.button('Рассчитать'):
        if not len(user_date_input) == 2 or not park or not poligon:
            st.write('Заполните все поля')
        elif len(user_date_input) == 2 and park and poligon:
            user_date_input = tuple(map(pd.to_datetime, user_date_input))
            start_date, end_date = user_date_input
            result = result.loc[result['Дата'].between(start_date, end_date)]
            result = result[result['Наименование структурного подразделения'] == park]

            data_cat = data_cat.loc[data_cat['Дата'].between(start_date, end_date)]

            mean_rating_park = data_cat[data_cat['Наименование структурного подразделения'] == park]['grade'].mean()
            st.markdown(f"### Средний рейтинг подразделения {park} равен <span style='color:red;'>{mean_rating_park:.03}</span>", unsafe_allow_html=True)
            mean_rating_poligon = data_cat[data_cat['Наименование полигона'] == poligon]['grade'].mean()
            st.markdown(f"### Средний рейтинг полигона {poligon} равен <span style='color:red;'>{mean_rating_poligon:.03}</span>", unsafe_allow_html=True)

        
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

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=result['Дата'], 
                y=result['Номера машин, которые целевые, но ездили, хотя не должны'].map(len),  # Замените 'grade' на соответствующий столбец для i-той линии
                mode='lines',
                line=dict(color='blue'),
                name=f'Номера машин, которые целевые, но ездили, хотя не должны'  # Добавьте подходящее имя для каждой линии
            ))


            fig.update_layout(
                title=f'Машины в парке, которые совершали поездки без плана в путевых листах',
                xaxis_title='Дата',
                yaxis_title='Количество машин',
                legend=dict(x=0, y=1),
                width=800,
                height=400
            )

            # Отображение графика в Streamlit
            st.plotly_chart(fig)

            st.header('Информация о ТС на уровне Полигона')  
            st.dataframe(give_chillusha(result))

            # if park:
            #     park_list = dict_poligon_park.get(poligon) 
            #     data_park = give_chillusha(result, 
            #                                 '2024-04-01', 
            #                                 '2024-04-30', 
            #                                 group_by_column='Наименование структурного подразделения', 
            #                                 aggregate_column='Номера в целевой структуре парка')
            st.header('Информация о ТС на уровне Подразделения') 
            st.dataframe(give_chillusha(result, 
                                            '2024-04-01', 
                                            '2024-04-30', 
                                            group_by_column='Наименование структурного подразделения', 
                                            aggregate_column='Номера в целевой структуре парка'))




   
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
