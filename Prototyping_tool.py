#!/usr/bin/env python
# coding: utf-8

import warnings
import pickle
import pandas as pd
import numpy as np
import xgboost as xgb
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from Data_Prep_Tools import prep_df
from Geocoder import *

from os import path
file_path = path.abspath(__file__) # full path of your script
dir_path = path.dirname(file_path) # full path of the directory of your script
temp_df_path = path.join(dir_path,'temp_df.pickle') 
sale_knn_path = path.join(dir_path,'sale_knn.pickle') 
rent_knn_path = path.join(dir_path,'rent_knn.pickle') 
xgb_path = path.join(dir_path,'xgb.pickle') 



warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore')


def invest(x):
    return 'invest' in x.lower()

def dorm(x):
    return 'bendrab' in x.lower()

def geocode_row(row, delay=0):
    df = pd.DataFrame([row, row])
    df['House number'].fillna('', inplace=True)
    df['Address'] = df['Address'].apply(lambda s : s.split('.')[0] + '.')
    df['Address'] = df['Address'] + ' ' + df['House number']

    geolocator = Nominatim(user_agent="Aruodas_predictor")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=delay)
    df['Location'] = df['Address'].apply(geocode)            
    df['Address'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(fix_address)
    df['Location'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(geocode)
    df['Latitude'] = df['Location'].apply(lat)
    df['Longitude'] = df['Location'].apply(long)
    df.drop('Location', axis=1, inplace=True)
    return df.iloc[1]


def prep_ml_row(row, return_price=False, dictionary=True):

    MEANS = {'Kindergarden': 369.01230861603153,
    'School': 462.5607925547886,
    'Shop': 324.0048033623534,
    'Bus': 199.07067669172923}

    row = geocode_row(row)
    row = prep_df(pd.DataFrame([row]))


    with open(temp_df_path, 'rb') as handle:
        temp_df = pickle.load(handle)

    temp_df = temp_df.append(row)
    temp_df.drop('Heating estimate', axis=1, inplace=True)

    for k, i in MEANS.items():
        temp_df[k].fillna(i, inplace=True)



    temp_df.fillna(0, inplace=True)
    temp_df['Bendrabutis'] = temp_df['Comment'].apply(dorm)*1
    temp_df['Investicija'] = temp_df['Comment'].apply(invest)*1
    temp_df['eur/m2'] = temp_df['Price']/temp_df['Area']

    with open(sale_knn_path, 'rb') as handle:
        neigh = pickle.load(handle)

    temp_df['eur/m2_p'] = neigh.predict(temp_df[['Latitude', 'Longitude']])[0][0]

    with open(rent_knn_path, 'rb') as handle:
        neigh = pickle.load(handle)

    temp_df['eur/m2_rent_p'] = neigh.predict(temp_df[['Latitude', 'Longitude']])[0][0]

    temp_df['Predicted rent'] = temp_df['eur/m2_rent_p']*temp_df['Area'] #
    temp_df['Predicted sale'] = temp_df['eur/m2_p']*temp_df['Area'] #
    temp_df['ROI'] = (temp_df['Predicted rent']/temp_df['Predicted sale'])*12 #

    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64', 'uint8'] #
    temp_df = temp_df.select_dtypes(include=numerics) #
    temp_df.drop('eur/m2', axis=1, inplace=True) #


    real_price = temp_df['Price']
    if return_price:
        cols = ['Price',
                'Area',
                'Rooms',
                'Floor',
                'Floors',
                'Kindergarden',
                'School',
                'Shop',
                'Bus',
                'Broker number',
                'Owner number',
                'Latitude',
                'Longitude',
                'Renovated',
                'Built',
                'aeroterminis',
                'centrinis',
                'centriniskolektorinis',
                'dujinis',
                'elektra',
                'geoterminis',
                'kietukuru',
                'kita',
                'saulėsenergija',
                'skystukuru',
                'Atskiras įėjimas',
                'Aukštos lubos',
                'Butas palėpėje',
                'Butas per kelis aukštus',
                'Buto dalis',
                'Internetas',
                'Kabelinė televizija',
                'Nauja elektros instaliacija',
                'Nauja kanalizacija',
                'No misc',
                'Renovuotas namas',
                'Tualetas ir vonia atskirai',
                'Uždaras kiemas',
                'Virtuvė sujungta su kambariu',
                'Dušo kabina',
                'Indaplovė',
                'Kondicionierius',
                'No misc equip',
                'Plastikiniai vamzdžiai',
                'Rekuperacinė sistema',
                'Saldytuvas',
                'Sildomos grindys',
                'Skalbimo mašina',
                'Su baldais',
                'Virtuvės komplektas',
                'Viryklė',
                'Vonia',
                'Zidinys',
                'Balkonas',
                'Drabužinė',
                'No additional premises',
                'Pirtis',
                'Rūsys',
                'Sandėliukas',
                'Terasa',
                'Vieta automobiliui',
                'Yra palėpė',
                'Budintis sargas',
                'Kodinė laiptinės spyna',
                'No security features',
                'Sarvuotos durys',
                'Signalizacija',
                'Vaizdo kameros',
                'Dalinė apdaila ',
                'Kitas įrengimas',
                'Neįrengtas ',
                'Įrengtas',
                'Blokinis',
                'Karkasinis',
                'Kitas pastato tipas',
                'Medinis',
                'Monolitinis',
                'Mūrinis',
                'Rąstinis',
                'Bendrabutis',
                'Investicija',
                'eur/m2_p',
                'eur/m2_rent_p',
                'Predicted rent',
                'Predicted sale',
                'ROI']
    else:
        cols = ['Area',
                'Rooms',
                'Floor',
                'Floors',
                'Kindergarden',
                'School',
                'Shop',
                'Bus',
                'Broker number',
                'Owner number',
                'Latitude',
                'Longitude',
                'Renovated',
                'Built',
                'aeroterminis',
                'centrinis',
                'centriniskolektorinis',
                'dujinis',
                'elektra',
                'geoterminis',
                'kietukuru',
                'kita',
                'saulėsenergija',
                'skystukuru',
                'Atskiras įėjimas',
                'Aukštos lubos',
                'Butas palėpėje',
                'Butas per kelis aukštus',
                'Buto dalis',
                'Internetas',
                'Kabelinė televizija',
                'Nauja elektros instaliacija',
                'Nauja kanalizacija',
                'No misc',
                'Renovuotas namas',
                'Tualetas ir vonia atskirai',
                'Uždaras kiemas',
                'Virtuvė sujungta su kambariu',
                'Dušo kabina',
                'Indaplovė',
                'Kondicionierius',
                'No misc equip',
                'Plastikiniai vamzdžiai',
                'Rekuperacinė sistema',
                'Saldytuvas',
                'Sildomos grindys',
                'Skalbimo mašina',
                'Su baldais',
                'Virtuvės komplektas',
                'Viryklė',
                'Vonia',
                'Zidinys',
                'Balkonas',
                'Drabužinė',
                'No additional premises',
                'Pirtis',
                'Rūsys',
                'Sandėliukas',
                'Terasa',
                'Vieta automobiliui',
                'Yra palėpė',
                'Budintis sargas',
                'Kodinė laiptinės spyna',
                'No security features',
                'Sarvuotos durys',
                'Signalizacija',
                'Vaizdo kameros',
                'Dalinė apdaila ',
                'Kitas įrengimas',
                'Neįrengtas ',
                'Įrengtas',
                'Blokinis',
                'Karkasinis',
                'Kitas pastato tipas',
                'Medinis',
                'Monolitinis',
                'Mūrinis',
                'Rąstinis',
                'Bendrabutis',
                'Investicija',
                'eur/m2_p',
                'eur/m2_rent_p',
                'Predicted rent',
                'Predicted sale',
                'ROI']
    
    temp_df = temp_df[cols]
    if dictionary:
        temp_df = temp_df.to_dict(orient='records')[0]
    return temp_df

def predict(row):
    if isinstance(row, dict):
        row = pd.DataFrame([row])
    with open(xgb_path, 'rb') as handle:
        xgb = pickle.load(handle)
    prediction = np.expm1(xgb.predict(row)[0])
    return prediction
