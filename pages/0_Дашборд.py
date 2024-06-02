from filter_table import filter_dataframe

import streamlit as st

import plotly.graph_objects as go

import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
import altair as alt
import plotly.express as px
import streamlit_authenticator as stauth


import yaml
from yaml.loader import SafeLoader
import os

from dotenv import load_dotenv

load_dotenv()


MMDPR_LIST= ['test', 'test1']


st.set_page_config(page_title="Dashboard", 
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
    if username in MMDPR_LIST:
            data = data[data['Наименование структурного подразделения'] == 'Московская механизированная дистанция погрузочно-разгрузочных рабо#']
    st.write("**Параметры Дашборда**")

    grouped_data = filter_dataframe(data)
    grouped_data.groupby("Наименование структурного подразделения")
    st.dataframe(grouped_data)

    # raiting_tab(grouped_data)

    st.subheader("Суммарное значение пробега по Структурному подразделения")
    mask = ['Дата','Наименование структурного подразделения', 'Данные путевых листов, пробег']
    fig = px.bar(grouped_data[mask], x="Дата", y="Данные путевых листов, пробег", 
                    color="Наименование структурного подразделения", barmode="group")
    st.plotly_chart(fig, use_container_width=True)


    # Не выполнил поездку
    st.subheader("Коэффициент невыполненных поезок")
    fig = px.bar(grouped_data.groupby(["Дата", "Полигон"])["Не выполнил поездку"].mean().reset_index(), x="Дата", y="Не выполнил поездку", 
                    color="Полигон", barmode="group")
    st.plotly_chart(fig, use_container_width=True)


    # Штрафы по полигонам от пробег путевых листов
    st.subheader("Зависимость Штрафов по полигонам от Пробега на путевых листах")
    fig = go.Figure()
    for polygon in grouped_data["Полигон"].unique():
        fig.add_trace(go.Scatter(x=grouped_data[grouped_data["Полигон"] == polygon]["Данные путевых листов, пробег"], y=grouped_data[grouped_data["Полигон"] == polygon]["Штрафы"], mode="markers", name=polygon))
    fig.update_layout(xaxis_title="Пробег путевых листов", yaxis_title="Штрафы")
    st.plotly_chart(fig, use_container_width=True)

    # Манера вождения от Пробег телематики по номерным знакам ТС
    st.subheader("Зависимость Манеры вождения от Пробега телематики по номерным знакам ТС")
    fig = go.Figure()
    for polygon in grouped_data["Полигон"].unique():
        fig.add_trace(go.Scatter(x=grouped_data[grouped_data["Полигон"] == polygon]["манера вождения"], y=grouped_data[grouped_data["Полигон"] == polygon]["Данные телематики, пробег"], mode="markers", name=polygon))
    fig.update_layout(xaxis_title="Манера вождения", yaxis_title="Пробег телематики")
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("Пробег и Телеметрия")
    fig = go.Figure()

    # Добавляем точки для каждого полигона
    for polygon in grouped_data["Полигон"].unique():
        fig.add_trace(go.Scatter(x=grouped_data[grouped_data["Полигон"] == polygon]["Данные путевых листов, пробег"], 
                                y=grouped_data[grouped_data["Полигон"] == polygon]["Данные телематики, пробег"], 
                                mode="markers", name=polygon))

    # Добавляем линии y = x + 60 и y = x - 60
    x = grouped_data["Данные путевых листов, пробег"]
    fig.add_trace(go.Scatter(x=x, y=x + 60, mode="lines", name="y = x + 60", line=dict(color="gray", dash="solid", width = 1.3)))
    fig.add_trace(go.Scatter(x=x, y=x - 60, mode="lines", name="y = x - 60", line=dict(color="gray", dash="solid", width = 1.3)))

    fig.update_layout(xaxis_title="Данные путевых листов, пробег", 
                    yaxis_title="Данные телематики, пробег",
                    )

    st.plotly_chart(fig, use_container_width=True)
   
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')