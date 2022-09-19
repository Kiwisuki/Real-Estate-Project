# coding: utf-8
'''This script is used to process data from the raw database
    and insert it to the processed database'''
import logging
import pandas as pd
from pymongo import MongoClient
from raw_data_processing_tools import process_df

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',\
     level=logging.INFO, datefmt='%I:%M:%S')


USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority"
AD_TYPES = ['butai/vilniuje', 'butu-nuoma/vilniuje', 'butai/kaune', 'butu-nuoma/kaune']


def get_unprocessed_rows(ad_type, limit=100):
    '''Get unprocessed rows from database'''
    cluster = MongoClient(PROCCESSED_DATABASE)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    ids = collection.distinct('Id')

    cluster = MongoClient(RAW_DATABASE)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    rows = list(collection.find({'Id': {'$nin': ids}}).limit(limit))
    printer = lambda x: logging.info(f'Id: {x["Id"]}')
    list(map(printer, rows))

    return rows

def insert_rows(rows_to_insert, ad_type, database_query=PROCCESSED_DATABASE):
    '''Insert rows to database'''
    cluster = MongoClient(database_query)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    collection.insert_many(rows_to_insert)

def processing_epoch():
    '''Process one epoch of data'''
    for ad_type in AD_TYPES:
        rows = get_unprocessed_rows(ad_type, 10)
        if len(rows) < 10:
            continue
        df = pd.DataFrame(rows)
        df = process_df(df)
        df = df.drop('_id', axis=1)
        rows = df.to_dict(orient='records')
        insert_rows(rows, ad_type)
        logging.info(f'Processed 10 rows, Ad type: {ad_type}')

def main():
    '''Main function'''
    while True:
        processing_epoch()

if __name__ == '__main__':
    main()

