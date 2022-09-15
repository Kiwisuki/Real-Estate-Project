# coding: utf-8
'''This script is used to scrape data from the website'''
import logging
import random
from importlib import reload
from scraping_tools import scrape_type_links, scrape_ad,\
     prepoc_row, insert_to_db, get_ids, filter_links

reload(logging)
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')

def main():
    '''Main function'''
    nts = ['butai/vilniuje', 'butu-nuoma/vilniuje']
    while True:
        for nt in nts:
            links, thumbs = scrape_type_links(nt)
            links, thumbs = filter_links(links, thumbs, get_ids(nt))
            random.shuffle(links)
            count = 0
            for link, thumb in zip(links, thumbs):
                logging.info(f'{len(links) - count} ads left, scraped {count} ads, Type: {nt}')
                try:
                    ad_row = scrape_ad(link, AdType=nt, Thumbnail=thumb)
                    ad_row = prepoc_row(ad_row)
                    insert_to_db(ad_row, collection_name=nt)
                    count += 1
                except KeyboardInterrupt:
                    logging.info('Interrupting program, good night :)')
                    raise
                except Exception as exception:
                    logging.critical(f'DANGER:{exception}')


if __name__ == '__main__':
    main()


