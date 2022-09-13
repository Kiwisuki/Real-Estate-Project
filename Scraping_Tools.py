# coding: utf-8
'''This module contains all the functions for scraping data from the website'''
import re
import time
from datetime import datetime
import logging
import bs4
import numpy as np
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from pymongo import MongoClient


USER = 'Kiwisuki'
PASSWORD = 'slaptazodis'
DB_NAME = 'Real-Estate'
RAW_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}\
    @real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"
PROCCESSED_DATABASE = f"mongodb+srv://{USER}:{PASSWORD}\
    @real-estate.cduph5g.mongodb.net/?retryWrites=true&w=majority"


def get_html(link:str, depth=0):
    """Get html version of page with loaded javascript parts by using undetectable selenium driver
    Args:
        link: a full link for the page to get html from
    Returns:
        txt: html code of a page
    """
    ua = UserAgent()
    try:
        opts = uc.ChromeOptions()
        opts.add_argument(f"user-agent={ua.random}")
        opts.headless = True
        driver = uc.Chrome(options=opts)
        driver.get(link)
        txt = driver.page_source
        driver.quit()
        logging.debug(f'Request sent successfully: {link}')
        return txt
    except Exception as exception:
        if depth < 3:
            logging.warning(f'Get Error: {link}  \n \n {exception}')
            time.sleep(3)
            return get_html(link, depth=depth+1)
        else:
            logging.error(f'Get Error: {link}  \n \n {exception}')
            raise exception

def parse_ad(html_text:str, **kwargs):
    """Parses ad for attributes available, except: heating
    Args:
        html_text: html text file saved from website
        nt: type of real estate to parse
    Returns:
        row: a dictionary of all scraped values from Real Estate ad
    """

    soup = bs4.BeautifulSoup(str(html_text), 'lxml')

    # Standard numerical/categorical features from the tables extraction
    row_values = soup.find_all('dd')
    row_names = soup.find_all('dt')
    row_values.extend(soup.find_all(class_='cell-data'))
    row_names.extend(soup.find_all(class_='cell-text'))

    row = {}
    for value, name in zip(row_values, row_names):
        value = re.sub(' +', ' ', value.text.replace('\n', ' '))
        name = re.sub(' +', ' ', name.text.replace('\n', ' '))
        row[name] = value

    row['Address'] = re.sub(' +', ' ', soup.find('h1').text.replace('\n', ' '))
    row['Price'] = (soup.find('span', class_='price-eur').text.replace(' ', '')).replace('\n', '')

    try:
        photos = [a['href'] for a in soup.find_all('a', class_='link-obj-thumb')]
        hidden_photos = [a['href'] for a in soup.find_all('a', class_='link-obj-thumb hide')]
        photos.extend(hidden_photos)
        photos = list(filter(lambda x: 'img.dgn' in x, photos))
        row['Photos'] = list(set(photos))
    except Exception:
        sold = soup.find_all(class_='adv-sold1-lt')
        row['Sold'] = len(sold) > 0


    row['Date scraped'] = datetime.today().strftime('%Y-%m-%d')
    row['Id'] = row['Nuoroda'].split('/')[1]


    try:
        row['Comment'] = str(soup.find(class_='obj-comment').text)
    except:
        logging.warning(f'No comment for {row["Nuoroda"]}')


    try:
        row['Broker number'] = str(soup.find(class_='phone_item_0').text)
    except:
        try:
            row['Owner number'] = str(soup.find(class_='phone').text)
        except:
            logging.warning(f'No phone number for {row["Nuoroda"]}')



    for key, value in kwargs.items():
        row[key] = value

    logging.debug(f'Row parsed successfully')
    return row

def parse_links(html_text):
    """Scrapes and returns all ad links found on ad list
    Args:
        html_text: html text file saved from website
    Returns:
        links: a list of all ad links found on website
    """
    soup = bs4.BeautifulSoup(html_text, 'lxml')
    posts = soup.find_all('tr', class_='list-row')
    
    links = []
    thumbs = []
    for post in posts:
        link = post.find('a', href=True)
        try:
            links.append(link['href']) 
        except Exception:
            pass
        
        try:
            thumbs.append(post.find('div', class_='list-photo').find('img')['src'])
        except Exception:
            thumbs.append('')
    logging.info(f'Found ads: {len(links)}')
    return links, thumbs

def get_last_page(html_text):
    """Scrapes and returns last page number from ad list
    Args:
        html_text: html text file saved from website
    Returns:
        last_page: a number of last page in ad list
    """
    soup = bs4.BeautifulSoup(html_text, 'html.parser')
    result = int(soup.find_all(class_='page-bt')[-2].text.replace(' ', '').replace('\n', ''))
    logging.info(f'Last page found: {result}')
    return result

def is_link_used(link, scraped_ids):
    # Helper method
    return not any(substring in link for substring in scraped_ids)

def is_valid_url(url):
    '''Checks if url is valid'''
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def filter_links(links:list, thumbs:list, scraped_ids:list):
    """Filters out links that have already been scraped
    Args:
        links: a list of all ad links found on website
        scraped_ids: a list of all ad links that have already been scraped
    Returns:
        links: a list of all ad links found on website that have not been scraped
    """
    before = len(links)
    print(scraped_ids)
    scraped_ids = np.array(scraped_ids)
    links = np.array(links)

    thumbs = [t for t in thumbs if t != ''] # ! No clue how these values end up here
    thumbs = np.array(thumbs)
    
    used_filter = np.array([is_link_used(row, scraped_ids) for row in links])
    valid_filter = np.array([is_valid_url(row) for row in links])

    final_filter = used_filter & valid_filter
    print (links)
    print(thumbs)
    links = links[final_filter]
    thumbs = thumbs[final_filter]

    after = len(links)
    logging.debug(f'Before filter: {before}, after: {after}, filtered {before - after} rows')
    return list(links), list(thumbs)

def scrape_type_links(ad_type:str):
    """Scrapes and returns all ad links found on all city pages
    Args:
        nt: what type of ad to scrape(house, flat, etc)
    Returns:
        city_links: a list of all city ad links found on Aruodas.lt
    """
    ad_types = ['butai', 'butu-nuoma', 'namai', 'patalpos',\
                'namu-nuoma', 'patalpu-nuoma', 'butai/vilniuje', 'butu-nuoma/vilniuje']
    if ad_type not in ad_types:
        raise ValueError('Invalid type')

    city_links = []
    city_thumbs = []

    call = 'https://www.aruodas.lt/{}/puslapis/{}/'
    city_html = get_html(f'https://www.aruodas.lt/{ad_type}/puslapis/1/')
    last_page = get_last_page(city_html)

    for i in range(1, last_page+1):
        txt = get_html(call.format(ad_type, i))
        links, thumbs = parse_links(txt)
        city_links.extend(links)
        city_thumbs.extend(thumbs)
    return city_links, city_thumbs

def get_ids(nt):
    '''Returns a list of all scraped ids'''
    with MongoClient(RAW_DATABASE) as cluster:
        db = cluster[DB_NAME]
        collection = db[nt]
        return [x['Id'] for x in collection.find({}, {'Id':1, '_id':0})]

def scrape_ad(link, **kwargs):
    '''Scrapes a single ad'''
    txt = get_html(link)
    row = parse_ad(txt, **kwargs)
    logging.info(f'Scraped {link}')
    return row

def insert_to_db(row, collection_name, database=RAW_DATABASE):
    '''Inserts a single ad to database'''
    with MongoClient(database) as cluster:
        db = cluster[DB_NAME]
        collection = db[collection_name]
        collection.insert_one(row)

def prepoc_row(row):
    '''Prepares a single ad for insertion to database'''
    new = {}
    for key, value in row.items():
        new_key = " ".join(key.split()).replace(':','')
        new[new_key] = value
    return new
