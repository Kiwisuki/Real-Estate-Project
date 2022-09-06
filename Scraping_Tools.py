# coding: utf-8
import re
import time
from datetime import datetime
import logging
import cchardet

import bs4
import numpy as np
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from pymongo import MongoClient

OLD_COLS = ['Namo numeris',
 'Plotas',
 'Kambarių sk.',
 'Aukštas',
 'Aukštų sk.',
 'Metai',
 'Pastato tipas',
 'Šildymas',
 'Įrengimas',
 'Ypatybės',
 'Papildoma įranga',
 'Nuoroda',
 'Įdėtas',
 'Redaguotas',
 'Įsiminė',
 'Peržiūrėjo',
 'Artimiausias darželis',
 'Artimiausia mokymo įstaiga',
 'Artimiausia parduotuvė',
 'Viešojo transporto stotelė',
 'Address',
 'Price',
 'date_scraped',
 'id',
 'Real Estate Type',
 'Comment',
 'Broker number',
 'Pastato energijos suvartojimo klasė',
 'Papildomos patalpos',
 'Apsauga',
 'Aktyvus iki',
 'Owner number',
 'Buto numeris',
 'Thumbnail']

NEW_COLS = ['House number',
 'Area',
 'Rooms',
 'Floor',
 'Floors',
 'Year',
 'Building type',
 'Heating',
 'Finish',
 'Misc',
 'Misc equipment',
 'Link',
 'Uploaded',
 'Edited',
 'Saved',
 'Seen',
 'Kindergarden',
 'School',
 'Shop',
 'Bus',
 'Address',
 'Price',
 'Date scraped',
 'id',
 'Real estate type',
 'Comment',
 'Broker number',
 'Energy class',
 'Additional premises',
 'Security',
 'Active until',
 'Owner number',
 'Flat number',
 'Thumbnail',]

class BotDetectedException(Exception):
    pass

def get_html(link, depth=0):
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

def parse_ad(html_text, nt, thumb):
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

    try:
        price = (soup.find('span', class_='price-eur').text.replace(' ', '')).replace('\n', '')
    except Exception as exception:
        logging.error(f'Error from price detection: {exception}')
        raise BotDetectedException

    address = re.sub(' +', ' ', soup.find('h1').text.replace('\n', ' '))
    row['Address'] = address
    row['Price'] = price

    # Features extraction from thumbs of the ad
    titles = []
    ids = []
    thumbs = soup.find_all(class_='obj-thumb') 

    '''
    try:
        for t in thumbs:
            try:
                # If thumb has title, it is a photo
                titles.append(t['title'])
            except KeyError:
                try:
                    # If it has data-type it is misc,- video, maps or 3d tour
                    ids.append(t['data-type'])
                except KeyError:
                    pass
        last_thumb = titles[-1].split('-')[-1]
        row['N_photos'] = [int(s) for s in last_thumb.split() if s.isdigit()][0]
        row['3d_tour'] = ('3d' in ids)
        row['video'] = ('video' in ids)
    except IndexError:
        row['N_photos'] = 0
        row['3d_tour'] = False
        row['video'] = False
        sold = soup.find_all(class_='adv-sold1-lt')
        row['sold'] = len(sold) > 0
    '''


    row['date_scraped'] = datetime.today().strftime('%Y-%m-%d')
    row['id'] = row['Nuoroda'].split('/')[1]
    row['Real Estate Type'] = nt
    

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


    row['Thumbnail'] = thumb
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
    soup = bs4.BeautifulSoup(html_text, 'html.parser')
    result = int(soup.find_all(class_='page-bt')[-2].text.replace(' ', '').replace('\n', ''))
    logging.info(f'Last page found: {result}')
    return result

def is_link_used(link, scraped_ids):
    # Helper method
    return not any(substring in link for substring in scraped_ids)

def is_valid_url(url):
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def filter_links(links, scraped_ids):
    try:
        scraped_ids = np.array(scraped_ids)
        links = np.array(links)
        
        bool_arr = np.array([is_link_used(row, scraped_ids) for row in links])
        links = links[bool_arr]
        
        bool_arr = np.array([is_valid_url(row) for row in links])
        links = links[bool_arr]
    except IndexError:
        return []

    return list(links)

def scrape_type_links(nt):
    """Scrapes and returns all ad links found on all city pages
    Args:
        nt: what type of ad to scrape(house, flat, etc)
    Returns:
        city_links: a list of all city ad links found on Aruodas.lt
    """
    nts = ['butai', 'butu-nuoma', 'namai', 'patalpos', 'namu-nuoma', 'patalpu-nuoma', 'butai/vilniuje', 'butu-nuoma/vilniuje']
    if nt not in nts:
        raise ValueError('Invalid type')

    city_links = []
    city_thumbs = []

    call = 'https://www.aruodas.lt/{}/puslapis/{}/'
    city_html = get_html(f'https://www.aruodas.lt/{nt}/puslapis/1/')
    last_page = get_last_page(city_html)

    for i in range(1, last_page+1):
        txt = get_html(call.format(nt, i))
        links, thumbs = parse_links(txt)
        city_links.extend(links)
        city_thumbs.extend(thumbs)
    return city_links, city_thumbs

def prepoc_row(row):
    new = {}
    for key in row:
        if type(row[key]) is str:
            new_key = " ".join(key.split()).replace(':','')
            new[new_key] = " ".join(row[key].split())
    return new

def get_ids(nt):
    with MongoClient("mongodb+srv://Kiwisuki:slaptazodis@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority") as cluster:
        db = cluster['Real-Estate']
        collection = db[nt]
        return [x['id'] for x in collection.find({}, {'id':1, '_id':0})]

def prep_row(row):
    prepped_row = {}
    for old, new in zip(OLD_COLS, NEW_COLS):
        try:
            prepped_row[new] = row[old]
        except KeyError:
            prepped_row[new] = np.nan
    return prepped_row

def scrape_ad(link, nt, thumb, save_to_db=True):
    txt = get_html(link)
    row = parse_ad(txt, nt, thumb)
    row = prepoc_row(row)
    row = prep_row(row)
    if save_to_db:
        with MongoClient("mongodb+srv://Kiwisuki:slaptazodis@real-estate.aaszr.mongodb.net/?retryWrites=true&w=majority") as cluster:
            db = cluster['Real-Estate']
            collection = db[nt]
            collection.insert_one(row)
    logging.info(f'Scraped {link}')
    return row
