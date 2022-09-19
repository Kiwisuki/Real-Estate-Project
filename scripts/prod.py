#!/usr/bin/env python
# coding: utf-8
from pymongo import MongoClient
import pandas as pd
import numpy as np
import warnings
import pickle
import re

from scraping_tools import scrape_ad
from raw_data_processing_tools import process_df
from scraping_tools import prepoc_row

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore')

USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority"

PRE_COLUMNS = ['Area', 'Rooms', 'Floor', 'Floors', 'Saved', 'Seen',
       'Nearest_kindergarden', 'Nearest_school', 'Nearest_store',
       'Nearest_bus_stop', 'Crimes', 'Price', 'Photos', 'Broker_number',
       'Average_heating_estimate', 'Owner_number', 'Renovated', 'Built',
       'Dorm', 'Days_active', 'Views_per_day', 'Saved_per_day',
       'Saves_per_views', 'eur_m2', 'Latitude', 'Longitude', 'eur_m2_rent_p',
       'Predicted rent', 'Invest', 'aeroterminis', 'centrinis',
       'centriniskolektorinis', 'dujinis', 'elektra', 'geoterminis',
       'kietukuru', 'kita', 'saulėsenergija', 'Atskiras įėjimas',
       'Aukštos lubos', 'Butas palėpėje', 'Butas per kelis aukštus',
       'Buto dalis', 'Internetas', 'Kabelinė televizija',
       'Nauja elektros instaliacija', 'Nauja kanalizacija',
       'Nėra papildomų ypatybių', 'Tualetas ir vonia atskirai',
       'Uždaras kiemas', 'Varžytynės/aukcionas',
       'Varžytynės/aukcionas buto dalis',
       'Varžytynės/aukcionas tualetas ir vonia atskirai',
       'Virtuvė sujungta su kambariu', 'Dušo kabina', 'Indaplovė',
       'Kondicionierius', 'Nėra papildomos įrangos', 'Plastikiniai vamzdžiai',
       'Rekuperacinė sistema', 'Saldytuvas', 'Sildomos grindys',
       'Skalbimo mašina', 'Su baldais', 'Virtuvės komplektas', 'Viryklė',
       'Vonia', 'Zidinys', 'Balkonas', 'Drabužinė', 'Nėra papildomų patalpų',
       'Pirtis', 'Rūsys', 'Sandėliukas', 'Terasa', 'Vieta automobiliui',
       'Yra palėpė', 'Budintis sargas', 'Kodinė laiptinės spyna',
       'No security features', 'Sarvuotos durys', 'Signalizacija',
       'Vaizdo kameros', 'Dalinė apdaila ', 'Kita_x', 'Nebaigtas statyti',
       'Neįrengtas ', 'Įrengtas', 'Blokinis', 'Karkasinis', 'Kita_y',
       'Medinis', 'Monolitinis', 'Mūrinis', 'Rąstinis', 'Comment_length']

COLUMNS = ['Area', 'Rooms', 'Floor', 'Floors', 'Saved', 'Seen',
       'Nearest_kindergarden', 'Nearest_school', 'Nearest_store',
       'Nearest_bus_stop', 'Crimes', 'Price', 'Photos', 'Broker_number',
       'Average_heating_estimate', 'Owner_number', 'Renovated', 'Built',
       'Dorm', 'Days_active', 'Views_per_day', 'Saved_per_day',
       'Saves_per_views', 'eur_m2', 'Latitude', 'Longitude', 'eur_m2_rent_p',
       'Predicted rent', 'Invest', 'aeroterminis', 'centrinis',
       'centriniskolektorinis', 'dujinis', 'elektra', 'geoterminis',
       'kietukuru', 'kita', 'saulėsenergija', 'Atskiras įėjimas',
       'Aukštos lubos', 'Butas palėpėje', 'Butas per kelis aukštus',
       'Internetas', 'Kabelinė televizija', 'Nauja elektros instaliacija',
       'Nauja kanalizacija', 'Nėra papildomų ypatybių',
       'Tualetas ir vonia atskirai', 'Uždaras kiemas',
       'Virtuvė sujungta su kambariu', 'Dušo kabina', 'Indaplovė',
       'Kondicionierius', 'Nėra papildomos įrangos', 'Plastikiniai vamzdžiai',
       'Rekuperacinė sistema', 'Saldytuvas', 'Sildomos grindys',
       'Skalbimo mašina', 'Su baldais', 'Virtuvės komplektas', 'Viryklė',
       'Vonia', 'Zidinys', 'Balkonas', 'Drabužinė', 'Nėra papildomų patalpų',
       'Rūsys', 'Sandėliukas', 'Terasa', 'Vieta automobiliui', 'Yra palėpė',
       'Budintis sargas', 'Kodinė laiptinės spyna', 'No security features',
       'Sarvuotos durys', 'Signalizacija', 'Vaizdo kameros', 'Dalinė apdaila ',
       'Kita_x', 'Neįrengtas ', 'Įrengtas', 'Blokinis', 'Kita_y',
       'Monolitinis', 'Mūrinis', 'Comment_length']

cluster = MongoClient(PROCCESSED_DATABASE)
db = cluster[DB_NAME]
collection = db['butai/vilniuje']
df = pd.DataFrame([i for i in collection.find()])

def prep(x):
    rez = ''
    for i in x:
        rez+=i + ';'
    return rez

def predict(row, fold):
    df = pd.DataFrame([row])

    with open("rent_knn.pickle", "rb") as f:
        neigh = pickle.load(f)

    df['eur_m2_rent_p'] = neigh.predict(df[['Latitude', 'Longitude']])
    df['Predicted rent'] = df['eur_m2_rent_p']*df['Area'] 
    df['Invest'] = df['Comment'].apply(lambda x: ('invest' in x.lower())*1)
    df['Owner_number'] = df['Owner_number'].notna()*1
    df['Broker_number'] = df['Broker_number'].notna()*1

    feats = df['Heating'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Misc'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Additional_equipment'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Additional_spaces'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Security_features'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = pd.get_dummies(df['Finish'])
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = pd.get_dummies(df['Building_type'])
    df = pd.merge(df, feats, left_index=True, right_index=True)

    df = df.drop(['Heating', 'Misc', 'Additional_equipment', 'Additional_spaces',\
         'Security_features', 'Address', 'AdType'], axis=1)

    df['Photos'] = df['Photos'].apply(len)
    df['Crimes'].replace(-1, np.nan, inplace=True)
    df['Predicted rent'] = df['Predicted rent']/0.005649405983081727

    df.set_index('_id', inplace=True)

    df['Comment_length'] = df['Comment'].apply(len)
    df = df.select_dtypes('number')

    for col in df:
        df[col] = df[col].fillna(df[col].mean())

    for col in PRE_COLUMNS:
        if col not in df:
            df[col] = 0

    euw = ['Varžytynės/aukcionas', 'Varžytynės/aukcionas buto dalis', 'Medinis', 'Rąstinis',\
        'Buto dalis', 'Karkasinis', 'Nebaigtas statyti', \
            'Varžytynės/aukcionas tualetas ir vonia atskirai', 'Pirtis']
    df.drop(euw, axis=1, inplace=True)

    df = df[COLUMNS]
    X = df.drop(['Price' ,'eur_m2'], axis=1)
    y  = df['Price']
    with open(f"model_{fold}.pickle", "rb") as f:
        model = pickle.load(f)

    x = X.values[0]
    y = y.values[0]
    return int(round(np.expm1(model.predict(x)), -2)), int(y)

def get_id(x):
    id_ = re.search('[0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9]', x)[0]
    return id_

def get_fold(id_):
    with open("fold_ids.pickle", "rb") as f:
        ids = pickle.load(f)
    for i in range(len(ids)):
        if id_ in ids[i]:
            return i+1
    return 1

def get_prediction(link):
    id_ = get_id(link)
    url = f'https://www.aruodas.lt/{id_}'
    row = scrape_ad(url)
    row = prepoc_row(row)
    row = pd.DataFrame([row])
    row = process_df(row)
    row = row.to_dict('records')[0]
    fold = get_fold(id_)
    prediction, real = predict(row, fold)
    return prediction, real