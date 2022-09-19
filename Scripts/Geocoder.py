import time
import math
import logging
import warnings
from importlib import reload

import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from pymongo import MongoClient

warnings.filterwarnings('ignore')
reload(logging)
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')

USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"


def fix_address(x):
    temp = x.split(',')
    return f'{temp[0]}, {temp[1]}'

def lat(location):
    try:
        return math.radians(location.latitude)
    except AttributeError:
        logging.info(f'Unable to get location')
        return np.nan

def long(location):
    try:
        return math.radians(location.longitude)
    except AttributeError:
        logging.info(f'Unable to get location')
        return np.nan

def get_count():   
    cluster = MongoClient('mongodb+srv://Kiwisuki:slaptazodis@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority')
    db = cluster['Real-Estate']
    collection = db['butai/vilniuje']
    sale_docs = collection.count_documents({ "Latitude" : { "$exists" : False },  "Longitude" : { "$exists" : False } })
    
    collection = db['butu-nuoma/vilniuje']
    sale_docs += collection.count_documents({ "Latitude" : { "$exists" : False },  "Longitude" : { "$exists" : False } })
    return sale_docs

def main():
    nts = ['butai/vilniuje', 'butu-nuoma/vilniuje']
    while True:
        while get_count() > 0:
            for category in nts:
                cluster = MongoClient('mongodb+srv://Kiwisuki:slaptazodis@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority')
                db = cluster['Real-Estate']
                collection = db[category]
                df = pd.DataFrame([i for i in collection.find({ "Latitude" : { "$exists" : False },  "Longitude" : { "$exists" : False } }).limit(5)])
                if len(df) == 0:
                    continue
                df['House number'].fillna('', inplace=True)
                df['Address'] = df['Address'].apply(lambda s : s.split('.')[0] + '.')
                df['Address'] = df['Address'] + ' ' + df['House number']

                geolocator = Nominatim(user_agent="Aruodas_predictor")
                geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
                df['Location'] = df['Address'].apply(geocode)            
                df['Address'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(fix_address)
                df['Location'][df['Location'].isna()] = df['Address'][df['Location'].isna()].apply(geocode)
                df['Latitude'] = df['Location'].apply(lat)
                df['Longitude'] = df['Location'].apply(long)
                df = df[['_id', 'Latitude', 'Longitude']]
                docs = df.to_dict(orient='records')
                for doc in docs:
                    collection.update_one({'_id':doc['_id']}, {"$set": {"Latitude": doc['Latitude'], 'Longitude': doc['Longitude']}}, upsert=False)
                    logging.info(f'Updated {doc["_id"]} ')
        logging.info(f'Sleeping for 30min')
        time.sleep(1800)


if __name__ == '__main__':
    main()
