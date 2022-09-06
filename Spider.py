import logging
import random
from importlib import reload

from Scraping_Tools import *

reload(logging)
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')

def main():
    nts = ['butai/vilniuje', 'butu-nuoma/vilniuje']
    while True:
        for nt in nts:
            links, thumbs = scrape_type_links(nt)
            links = filter_links(links, get_ids(nt))
            random.shuffle(links)
            for idx, link in enumerate(links):
                logging.info(f'{len(links) - idx} ads left to scrape, scraped {idx} ads, Type: {nt}')
                try:
                    scrape_ad(link, nt, thumbs[idx])
                except BotDetectedException:
                    logging.info('Bot detected, skipping')
                except KeyboardInterrupt:
                    logging.info('Interruptin program, good night :)')
                    raise
                except Exception as e:
                    logging.critical(f'DANGER:{e}')


if __name__ == '__main__':
    main()
