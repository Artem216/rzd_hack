import streamlit as st
import pandas as pd
import os
import components.data_preprossesing as dp 

 
st.set_page_config(page_title="Загрузка данных", 
                   page_icon="💾",
                   layout="wide")
st.title("Загрузка данных")

sidebar = st.sidebar

import base64
import streamlit as st

# @st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_background('data/cars.jpg')

col1, col2, col3 = st.columns(3)

# with col1:
#     st.image('./data/flower.jpg', width=100)

uploaded_file = st.file_uploader("Выберите Excel файл", type="xlsx")

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    st.write("Данные:")
    st.dataframe(data)

    path_save_data = './data/data.xlsx'
    path_data_rdy = './data/data_rdy.xlsx'
    if os.path.exists(path_save_data):
        os.remove(path_save_data)
    if os.path.exists(path_data_rdy):
        os.remove(path_data_rdy)
    data.to_excel(path_save_data, index=False)
    dp.preprossesing_data(data).to_excel(path_data_rdy, index=False)


# Загрузка данных.py