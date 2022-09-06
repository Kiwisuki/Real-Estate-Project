import re
import warnings
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

def area(x):
    try:
        x = re.sub('[^0-9.]', "", x.replace(",","."))
        if x == '':
            return 0
        return x
    except:
        return np.nan

def distance(x):
    if pd.isnull(x):
        return np.NaN
    dist = re.sub('[^0-9.]', "", x.replace(",","."))
    if 'km' in x:
        dist = float(dist)*1000
    return float(dist)

def heating(x):
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
    x = x.replace('Š', 'S')
    x = x.replace('Ž', 'Z')
    r = re.findall('[A-Z][^A-Z]*', x)
    rez = []
    for i in r:
        rez.append(i.strip(' '))
    return rez

def prep(x):
    rez = ''
    for i in x:
        rez+=i + ';'
    return rez

def snipper(x):
    x = x.lower()
    x = x.replace(' ','')
    return x.split(',')

def prep_df(df):
    df['Misc'].fillna('No misc', inplace=True)
    df['Misc equipment'].fillna('No misc equip', inplace=True)
    df['Additional premises'].fillna('No additional premises', inplace=True)
    df['Energy class'].fillna(' D? ', inplace=True)
    df['House number'].fillna('', inplace=True)


    df['Price'] = df['Price'].apply(lambda s : s.strip('€'))
    df['Area'] = df['Area'].astype(str)
    df['Year'] = df['Year'].astype(str)
    df['Area'] = df['Area'].apply(area).astype(float)
    df['Renovated'] = df['Year'].apply(lambda x : int(re.sub('[^0-9.]','',x)[-4:]))
    df['Built'] = df['Year'].apply(lambda x : int(re.sub('[^0-9.]','',x)[0:4]))
    df['Finish'] = df['Finish'].apply(lambda x : x.replace('NAUDINGA: Interjero dizaineriai',''))
    df['Bus'] = df['Bus'].apply(distance)
    df['Shop'] = df['Shop'].apply(distance)
    df['School'] = df['School'].apply(distance)
    df['Kindergarden'] = df['Kindergarden'].apply(distance)
    df['City'] = df['Address'].apply(lambda x : x.split()[0])

    df['Rooms'] = df['Rooms'].astype(int)
    df['Floor'] = df['Floor'].astype(int)
    df['Floors'] = df['Floors'].astype(int)
    df['Price'] = df['Price'].astype(float)

    df['Address'] = df['Address'].apply(lambda s : s.split('.')[0] + '.')
    df['Address'] = df['Address'] + ' ' + df['House number']
    df['Security'].fillna('No security features', inplace=True)
    df['Broker number'] = df['Broker number'].notna()*1
    df['Owner number'] = df['Owner number'].notna()*1


    df['Misc'] = df['Misc'].apply(splitter)
    df['Misc equipment'] = df['Misc equipment'].apply(splitter)
    df['Security'] = df['Security'].apply(splitter)
    df['Additional premises'] = df['Additional premises'].apply(splitter)



    df['Heating'] = df['Heating'].apply(snipper)

    to_drop = ['Active until', 'Flat number', 'Thumbnail', 'id', 'Date scraped', 'Edited', 'Saved', 'Seen', 'Uploaded', 'House number']
    df.drop(to_drop, axis=1, inplace=True)

    feats = df['Heating'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Misc'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Misc equipment'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Additional premises'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = df['Security'].apply(prep).str.get_dummies(';')
    df = pd.merge(df, feats, left_index=True, right_index=True)
    
    df['Finish'] = df['Finish'].replace({'Kita':'Kitas įrengimas'})
    df['Building type'] = df['Building type'].replace({'Kita':'Kitas pastato tipas'})


    feats = pd.get_dummies(df['Finish'])
    df = pd.merge(df, feats, left_index=True, right_index=True)

    feats = pd.get_dummies(df['Building type'])
    df = pd.merge(df, feats, left_index=True, right_index=True)

    df = df.drop(['Heating', 'Misc', 'Misc equipment', 'Additional premises', 'Security', 'Address', 'Real estate type'], axis=1)
    return df
