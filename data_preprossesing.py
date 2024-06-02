import pandas as pd
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

def preprossesing_data(data_):
    data = data_.copy()
    data = data.dropna(how='all')
    data = data.drop(['Выполняемые функции', 'Должность за кем закреплен ТС'], axis=1).reset_index(drop=True)
    correct_ind = list(set(range(data.shape[0])) - set(data[data['Наименование полигона'].notna()].index))
    wrong_ind = list(data[data['Наименование полигона'].notna()].index)
    cols = ['Наименование полигона',
            'Краткое наименование',
            'Полигон',
            'Номерной знак ТС',
            'Наименование структурного подразделения',
            'Тип закрепления', 
            'манера вождения']
    for col in cols:
        data[col] = data[col].ffill()
    
    # Делаем нужный формат времени
    def replace_year(date):
        if date.year == 2019:
            return date.replace(year=2024)
        return date
    data['дата путевого листа'] = pd.to_datetime(data['дата путевого листа'].apply(replace_year), format='%d-%m-%Y')
    data['Дата сигнала телематики'] = pd.to_datetime(data['Дата сигнала телематики'].apply(replace_year), format='%d-%m-%Y')

    
    # делаем попарные даты
    wrong_ind += [data.shape[0]]
    info_date = pd.DataFrame()
    for i in range(len(wrong_ind) - 1):
        gr1 = data.loc[wrong_ind[i]+1:wrong_ind[i+1]-1, cols[:-2] + ['дата путевого листа', 'Данные путевых листов, пробег', 'манера вождения', 'Штрафы', 'Тип закрепления']].rename(columns={'дата путевого листа': 'Дата'})
        gr2 = data.loc[wrong_ind[i]+1:wrong_ind[i+1]-1, cols[:-2] + ['Дата сигнала телематики', 'Данные телематики, пробег', 'манера вождения', 'Штрафы', 'Тип закрепления']].rename(columns={'Дата сигнала телематики': 'Дата'})
        info_date = pd.concat([info_date, pd.merge(gr1, gr2, on=cols[:-2] + ['Дата', 'манера вождения', 'Тип закрепления'], how='outer').dropna(how='all')]).reset_index(drop=True)
        info_date = info_date.dropna(subset=['Дата'], how='all')

    info_date['Штрафы'] = info_date[['Штрафы_x', 'Штрафы_y']].fillna(0).max(axis=1)
    data = info_date.drop(columns=['Штрафы_x', 'Штрафы_y'])

    data['Поездка не по плану'] = data.apply(lambda row: 1 if pd.isna(row['Данные путевых листов, пробег']) and not pd.isna(row['Данные телематики, пробег']) else 0, axis=1)
    data['Не выполнил поездку'] = data.apply(lambda row: 1 if not pd.isna(row['Данные путевых листов, пробег']) and pd.isna(row['Данные телематики, пробег']) else 0, axis=1)

    return data

def calculate_coefficient1(temp): # Кэф путевого отклонения
    if temp == 0:
        return 1
    elif temp >= 0.2:
        return 0.6
    elif temp >= 0.1:
        return 0.7
    else:
        return 0.8

def calculate_coefficient2(temp): # Кэф соответствия целевой структуре
    if temp == 0:
        return 1
    elif temp >= 0.2:
        return 0.6
    elif temp >= 0.1:
        return 0.7
    else:
        return 0.8

def calculate_coefficient3(temp): # Кэф манера вождения
    temp = 1 - temp/6 
    if temp == 0:
        return 1
    elif temp >= 0.2:
        return 0.7
    elif temp >= 0.15:
        return 0.8
    else:
        return 0.9

def calculate_coefficient4(temp, max_val):
    temp = temp/max_val
    if temp >= 0.2:
        return 0.7
    elif temp >= 0.15:
        return 0.8
    else:
        return 0.9

def assign_coefficient(value):
    if value == 0:
        return 1
    elif 1 <= value <= 5:
        return 0.8
    elif 6 <= value <= 12:
        return 0.7
    else:
        return 0.6

def add_rolling_mean_features(df, window_size):
    df = df.sort_values(by=['Наименование структурного подразделения', 'Дата'])
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    for col in numeric_cols:
        df[f'{col}_rolling_mean'] = df.groupby('Наименование полигона')[col].transform(lambda x: x.rolling(window=window_size, min_periods=1).mean())
    return df

def func_for_catboost(data_, range_pred):
    data = data_.copy()
    one_hot_encoder = OneHotEncoder()
    one_hot_encoded = one_hot_encoder.fit_transform(data[['Тип закрепления']])
    data_one_hot = pd.DataFrame(one_hot_encoded.toarray(), columns=one_hot_encoder.get_feature_names_out(['Тип закрепления']))
    data = pd.concat([data.drop('Тип закрепления', axis=1), data_one_hot], axis=1)
    # Агрегация
    aggregations = {
    'Данные путевых листов, пробег': 'sum',
    'Данные телематики, пробег': 'sum',
    'Штрафы': 'sum',
    'Тип закрепления_В целевой структуре парка': 'sum',
    'Тип закрепления_Прочие': 'sum',
    'манера вождения': 'mean',
    # 'Разница план_реальность(дни)': 'mean',
    'Поездка не по плану': 'max',
    'Не выполнил поездку': 'mean'#,
    # 'Кэф путевого отклонения': 'mean'
    }
    agg_cols = ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Наименование структурного подразделения', 'Дата']
    agg_data = data.groupby(agg_cols).agg(aggregations).reset_index()
    agg_data['количество записей'] = data.groupby(agg_cols).size().reset_index(name='количество записей')['количество записей']
    # расчет коэффициента 1
    agg_data['temp'] = abs(agg_data['Данные путевых листов, пробег'] - agg_data['Данные телематики, пробег']) / agg_data['Данные путевых листов, пробег']
    agg_data['Кэф путевого отклонения'] = agg_data['temp'].apply(lambda x: calculate_coefficient1(x))
    agg_data.drop(columns=['temp'], inplace=True)
    # расчет коэффициента 2
    agg_data['temp'] = abs(agg_data['Тип закрепления_В целевой структуре парка'] - agg_data['количество записей']) / agg_data['Тип закрепления_В целевой структуре парка']
    agg_data['Кэф соответствия целевой структуре'] = agg_data['temp'].apply(lambda x: calculate_coefficient2(x))
    agg_data.drop(columns=['temp'], inplace=True)
    # расчет коэффициента 3
    agg_data['Кэф манера вождения'] = data['манера вождения'].apply(lambda x: calculate_coefficient3(x))
    # agg_data.drop(columns=['манера вождения'], inplace=True)
    # расчет коэффициента 4
    # max_val = max(agg_data['Штрафы'])
    # agg_data['Кэф Штрафы'] = agg_data['Штрафы'].apply(lambda x: calculate_coefficient4(x, max_val))
    # print(agg_data['Штрафы'].value_counts())
    agg_data['Кэф Штрафы'] = agg_data['Штрафы'].apply(assign_coefficient)
    # agg_data['Кэф Штрафы'] = pd.qcut(agg_data['Штрафы'], q=[0, 0.9, 0.95, 1.0], labels=[0.9, 0.8], duplicates='drop').astype('int')
    # agg_data.drop(columns=['манера вождения'], inplace=True)
    # Подсчет оценки 
    agg_data['grade'] = 0.4*agg_data['Кэф путевого отклонения'] + 0.3*agg_data['Кэф соответствия целевой структуре'] + 0.15*agg_data['Кэф Штрафы'] + 0.15*agg_data['Кэф манера вождения']
    # Скользящее окно
    window_size = range_pred
    data_rolling_vals = add_rolling_mean_features(agg_data, window_size)
    # поменяем дату для модели
    # data_rolling_vals['День недели'] = data_rolling_vals['дата путевого листа'].dt.day_name()
    # data_rolling_vals['Дата'] = data_rolling_vals['дата путевого листа'].dt.day
    # data_rolling_vals = data_rolling_vals.drop(columns=['дата путевого листа'])
    return data_rolling_vals

def get_new_rating(df_):
    df = df_.copy()
    # df['манера вождения'] = df['манера вождения'].fillna(method='ffill')
    df['путевое отколение temp'] = 1 - abs(df['Данные путевых листов, пробег'] - df['Данные телематики, пробег'])
    df['соответствие целевой структуре temp'] = 1 - abs(df['Тип закрепления_В целевой структуре парка'] - df['количество записей'])
    df['Штраф temp'] = 1 - df['Штрафы']
    df['манера вождения temp'] = df['манера вождения']

    columns_to_scale = ['путевое отколение temp', 'соответствие целевой структуре temp', 'Штраф temp', 'манера вождения temp']
    scaler = MinMaxScaler()
    df[columns_to_scale] = scaler.fit_transform(df[columns_to_scale])
    df['Rating 2.0'] = 0.4*df['путевое отколение temp'] + 0.3*df['соответствие целевой структуре temp'] + 0.15*df['Штраф temp'] + 0.15*df['манера вождения temp']
    df.drop(columns=columns_to_scale, inplace=True)
    return df

def get_dicts_poligon_park(data_):
    dict_poligon_park, dict_park_poligon = {}, {}
    for poligon, park in set(zip(data_['Наименование полигона'], data_['Наименование структурного подразделения'])):
        if not isinstance(poligon, str) or not isinstance(park, str):
            continue
        if dict_poligon_park.get(poligon):
            dict_poligon_park[poligon].append(park)
        elif dict_park_poligon.get(park):
            dict_park_poligon[park].append(poligon)
        else:
            dict_poligon_park[poligon] = [park]
            dict_park_poligon[park] = [poligon]

    return dict_poligon_park, dict_park_poligon


def get_list_poligon(data_):
    return list(set(data_[data_['Наименование полигона'].notna()]['Наименование полигона']))

def get_list_park(data_):
    return list(set(data_[data_['Наименование структурного подразделения'].notna()]['Наименование структурного подразделения']))

def get_info_use(data_, poligon_name, park_name):
    data_rdy = data_.copy()
    group = data_rdy.groupby(
        ['Наименование полигона', 
        'Краткое наименование', 
        'Полигон', 
        'Наименование структурного подразделения']
    ).agg(
        in_use = pd.NamedAgg(column='Тип закрепления', 
                             aggfunc=lambda x: sum(x == 'В целевой структуре парка')),
        not_in_use = pd.NamedAgg(column='Тип закрепления', 
                             aggfunc=lambda x: sum(x == 'Прочие'))
    ).reset_index()

    row_info = group[(group['Наименование полигона'] == poligon_name) & 
                     (group['Наименование структурного подразделения'] == park_name)]
    
    return row_info['in_use'].values[0], row_info['not_in_use'].values[0]

def get_date_grade(data_rdy_, poligon, park):
    data = data_rdy_.copy()
    data = func_for_catboost(data, 1)

    data_park = data[(data['Наименование полигона'] == poligon) & 
                (data['Наименование структурного подразделения'] == park)]
    data_park = data_park[['Дата', 'grade']].sort_values('Дата')

    data_poligon = data[(data['Наименование полигона'] == poligon)]
    data_poligon_i = []
    for park_i in data_poligon['Наименование структурного подразделения'].unique():
        data_poligon_i.append(data_poligon[data_poligon['Наименование структурного подразделения'] == park_i][['Дата', 'grade']])
    
    data_poligon = data_poligon_i[0]
    for i in range(1, len(data_poligon_i)):
        data_poligon = data_poligon.merge(data_poligon_i[i], on='Дата', how='outer').sort_values('Дата')
    data_poligon['mean_grade'] = data_poligon.iloc[:, 1:].mean(1)
    data_poligon = data_poligon[['Дата', 'mean_grade']].sort_values('Дата')

    return data_park.merge(data_poligon, on='Дата', how='left').sort_values('Дата')
    