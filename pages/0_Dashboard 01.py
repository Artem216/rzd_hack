import streamlit as st
import pandas as pd
import os
import data_preprossesing as dp 
import altair as alt

st.set_page_config(page_title="Dashboard", 
                   page_icon= "1️⃣",
                   layout="wide")
st.title("Выбор")
col1, col2, col3 = st.columns(3)

path_save_file = './data/data.xlsx'
if not os.path.exists(path_save_file):
    st.write("Загрузите данные")

if os.path.exists(path_save_file):
    
    data = pd.read_excel('./data/data.xlsx')
    dict_poligon_park, dict_park_poligon = dp.get_dicts_poligon_park(data)

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
    with col1:
        if st.button('start'):
            if not isinstance(poligon, str) or not isinstance(park, str):
                st.write('Заполните все поля')
            else:
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
                    dy=-5  # Небольшое смещение вверх
                ).encode(
                    text='Количество машин:Q'
                )

                # Объединение графика и аннотаций
                chart = bars + text
                col1, col2, col3 = st.columns(3)
                with col2:
                    st.altair_chart(chart)

