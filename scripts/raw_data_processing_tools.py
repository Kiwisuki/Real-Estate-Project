#!/usr/bin/env python
# coding: utf-8

# Goal for preprocessed data:
# + Link(id) : string
# + Thumbnail_link: string
# + Name: string
# + Price: int
# + Predicted value: int
# + Predicted rent: int
# + ROI: float
# + Area: float
# + Rooms: int
# + Floor: int
# + Floors: int
# + Misc: categorical list
# + Bus: int
# + Shop: int
# + School: int
# + Kindergarden: int
# + City: categorical
# + District: categorical
# + Sold by Owner: boolean
# + Contact number: string
# + Heating: categorical
# + Finish: categorical
# + Date scraped: datetime
# + knn eur/m2: int
# + User clicks: int
# + Photo links: array
# + Heating Average: float
# + Comment: string
# + Address: string

import re
import warnings
import math
import pandas as pd
import numpy as np
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore')

USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority"

OLD_COLS = ['_id', 'Namo numeris', 'Buto numeris', 'Plotas', 'Kambarių sk.',
       'Aukštas', 'Aukštų sk.', 'Metai', 'Pastato tipas', 'Šildymas',
       'Įrengimas', 'Pastato energijos suvartojimo klasė', 'Ypatybės',
       'Papildomos patalpos', 'Papildoma įranga', 'Apsauga', 'Nuoroda',
       'Įdėtas', 'Redaguotas', 'Įsiminė', 'Peržiūrėjo',
       'Artimiausias darželis', 'Artimiausia mokymo įstaiga',
       'Artimiausia parduotuvė', 'Viešojo transporto stotelė',
       'Nusikaltimai 500 m spinduliu praėjusį mėnesį', 'Address', 'Price',
       'Photos', 'Date scraped', 'Id', 'Comment', 'Broker number', 'AdType',
       'Thumbnail', 'Reklama/pasiūlymas',
       'Vidutiniškai tiek kainuotų šildymas 1 mėn. Apskaičiuotas vidurkis iš skirtingų mėnesių ir skelbime nurodyto ploto',
       'Aktyvus iki', 'Owner number']
NEW_COLS = ['_id', 'House_number', 'Flat_number', 'Area', 'Rooms',
       'Floor', 'Floors', 'Year', 'Building_type', 'Heating',
       'Finish', 'Energy_class', 'Misc',
       'Additional_spaces', 'Additional_equipment', 'Security_features', 'Link',
       'Uploaded', 'Edited', 'Saved', 'Seen',
       'Nearest_kindergarden', 'Nearest_school',
       'Nearest_store', 'Nearest_bus_stop',
       'Crimes', 'Address', 'Price',
       'Photos', 'Date_scraped', 'Id', 'Comment', 'Broker_number', 'AdType',
       'Thumbnail', 'Advertisement',
       'Average_heating_estimate',
       'Active_until', 'Owner_number']
STR_COLS = ['House_number', 'Flat_number', 'Area', 'Rooms', 'Floor',
       'Floors', 'Year', 'Building_type', 'Heating', 'Finish', 'Energy_class',
       'Misc', 'Additional_spaces', 'Additional_equipment',
       'Security_features', 'Link', 'Uploaded', 'Edited', 'Saved', 'Seen',
       'Nearest_kindergarden', 'Nearest_school', 'Nearest_store',
       'Nearest_bus_stop', 'Crimes', 'Address', 'Price', 'Photos',
       'Date_scraped', 'Id', 'Comment', 'Broker_number', 'AdType', 'Thumbnail',
       'Advertisement', 'Average_heating_estimate', 'Active_until',
       'Owner_number']
    
strip_euro = lambda s : s.strip('€')
renovated = lambda x : int(re.sub('[^0-9.]','',x)[-4:])
built = lambda x : int(re.sub('[^0-9.]','',x)[0:4])
remove_advertisement = lambda x : x.replace('NAUDINGA: Interjero dizaineriai','')
extract_address = lambda s : s.split('.')[0] + '.'
city = lambda x : x.split(',')[0]
district = lambda x : x.split(',')[1]
extract_views = lambda x: int(x.split('/')[0])

def prepoc_str(x):
    '''removes empty spaces'''
    if isinstance(x, str):
        return " ".join(x.split())
    else:
        return x

def area(x):
    '''extracts area from string'''
    try:
        x = re.sub('[^0-9.]', "", x.replace(",","."))
        if x == '':
            return 0
        return x
    except:
        return np.nan

def distance(x):
    '''extracts distance from string'''
    if pd.isnull(x):
        return np.NaN
    d = re.sub('[^0-9.]', "", x.replace(",","."))
    if 'km' in x:
        d = float(d)*1000
    return float(d)

def heating(x):
    '''extracts heating type from string'''
    try:
        x = x.split('~')[0]
        x = x.replace('.','#')
        x = re.sub('[^0-9.]', "", x.replace(",","."))
        if x == '':
            return 0
        return x
    except:
        return np.nan
    
def splitter(x):
    '''splits string into list'''
    x = x.replace('Š', 'S')
    x = x.replace('Ž', 'Z')
    r = re.findall('[A-Z][^A-Z]*', x)
    rez = []
    for i in r:
        rez.append(i.strip(' '))
    return rez

def snipper(x):
    '''splits string into list'''
    x = x.lower()
    x = x.replace(' ','')
    return x.split(',')

def dorm(x):
    '''return whether flat is dormitory'''
    return ('bendrab' in x.lower())*1

def fix_address(x):
    '''summarizes address, removes street name'''
    a = x.split(',')
    return f'{a[0]}, {a[1]}'

def process_df(df):
    """Processes dataframe"""
    for col in OLD_COLS:
        if col not in df:
            df[col] = np.nan

    df = df[OLD_COLS]
    df = df.rename(dict(zip(OLD_COLS, NEW_COLS)), axis=1)

    df[STR_COLS] = df[STR_COLS].applymap(prepoc_str)
    df['Misc'].fillna('Nėra papildomų ypatybių', inplace=True)
    df['Additional_equipment'].fillna('Nėra papildomos įrangos', inplace=True)
    df['Additional_spaces'].fillna('Nėra papildomų patalpų', inplace=True)
    df['Energy_class'].fillna('Nežinoma', inplace=True)
    df['House_number'].fillna('', inplace=True)
    df['Flat_number'].fillna('', inplace=True)
    df['Saved'].fillna('0',inplace=True)
    df['Crimes'].fillna('-1',inplace=True)

    df['Price'] = df['Price'].apply(strip_euro)
    df['Area'] = df['Area'].astype(str)
    df['Year'] = df['Year'].astype(str)
    df['Area'] = df['Area'].apply(area).astype(float)
    df['Renovated'] = df['Year'].apply(renovated)
    df['Built'] = df['Year'].apply(built)
    df['Finish'] = df['Finish'].apply(remove_advertisement)
    df['Nearest_bus_stop'] = df['Nearest_bus_stop'].apply(distance)
    df['Nearest_store'] = df['Nearest_store'].apply(distance)
    df['Nearest_school'] = df['Nearest_school'].apply(distance)
    df['Nearest_kindergarden'] = df['Nearest_kindergarden'].apply(distance)
    df['City'] = df['Address'].apply(city)
    df['Average_heating_estimate'] = df['Average_heating_estimate'].apply(heating)
    df['District'] = df['Address'].apply(district)
    df['Rooms'] = df['Rooms'].astype(int)
    df['Floor'] = df['Floor'].astype(int)
    df['Floors'] = df['Floors'].astype(int)
    df['Crimes'] = df['Crimes'].astype(int)
    df['Crimes'].fillna(round(df['Crimes'].mean()), inplace=True)
    df['Price'] = df['Price'].astype(float)
    df['Address'] = df['Address'].apply(extract_address)
    df['Address'] = df['Address'] + ' ' + df['House_number']
    df['Security_features'].fillna('No security features', inplace=True)
    df['Misc'] = df['Misc'].apply(splitter)
    df['Additional_equipment'] = df['Additional_equipment'].apply(splitter)
    df['Security_features'] = df['Security_features'].apply(splitter)
    df['Additional_spaces'] = df['Additional_spaces'].apply(splitter)
    df['Heating'] = df['Heating'].apply(snipper)
    df['Seen'] = df['Seen'].apply(extract_views)
    df['Saved'] = df['Saved'].astype(int)
    df['Average_heating_estimate'] = df['Average_heating_estimate'].astype(float)
    df['Dorm'] = df['Comment'].apply(dorm)
    df['Uploaded'] = pd.to_datetime(df['Uploaded'])
    df['Date_scraped'] = pd.to_datetime(df['Date_scraped'])
    df['Average_heating_estimate'].fillna(df['Average_heating_estimate'].mean(), inplace=True)

    df['Days_active'] = (df['Date_scraped'] - df['Uploaded']).astype('timedelta64[h]')/24 + 1
    df['Views_per_day'] = df['Seen']/df['Days_active']
    df['Saved_per_day'] = df['Saved']/df['Days_active']
    df['Saves_per_views'] = df['Saved']/df['Seen']
    df['eur_m2'] = df['Price']/df['Area']

    df[['Views_per_day','Saved_per_day','Saves_per_views','eur_m2', 'Average_heating_estimate']] = \
    df[['Views_per_day','Saved_per_day','Saves_per_views','eur_m2', 'Average_heating_estimate']].round(2)

    df.drop('Active_until', axis=1, inplace=True)
    df.drop('Advertisement', axis=1, inplace=True)


    geolocator = Nominatim(user_agent="Aruodas_predictor")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    # First try
    df['Location'] = df['Address'].apply(geocode)

    # Fix addresses that did not work
    df['Address'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(fix_address)
    df['Location'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(geocode)

    # Save lat, long
    df['Latitude'] = df['Location'].apply(lambda x: math.radians(x.latitude))
    df['Longitude'] = df['Location'].apply(lambda x: math.radians(x.longitude))

    df.drop('Location', inplace=True, axis=1)
    return df
