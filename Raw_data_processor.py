from pymongo import MongoClient
from Raw_Data_Proccessing_Tools import process_df
import pandas as pd

USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority"
AD_TYPES = ['butai/vilniuje', 'butu-nuoma']


def get_unprocessed_rows(ad_type, n_rows):
    cluster = MongoClient(PROCCESSED_DATABASE)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    processed_ids = collection.distinct('Id')

    cluster = MongoClient(RAW_DATABASE)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    rows = list(collection.find({ "Id" : { '$nin': [processed_ids] }}).limit(n_rows))
    return rows

def insert_rows(rows_to_insert, ad_type, database_query=PROCCESSED_DATABASE):
    cluster = MongoClient(database_query)
    database = cluster[DB_NAME]
    collection = database[ad_type]
    collection.insert_many(rows_to_insert)

def processing_epoch():
    for ad_type in AD_TYPES:
        rows = get_unprocessed_rows(ad_type, 10)
        if len(rows) < 10:
            continue
        df = pd.DataFrame(rows)
        df = process_df(df)
        df = df.drop('_id', axis=1)
        rows = df.to_dict(orient='records')
        insert_rows(rows, ad_type)

if __name__ == '__main__':
    while True:
        processing_epoch()