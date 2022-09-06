from flask import Flask, redirect, url_for, render_template, request, session, json
from Scraping_Tools import *
from Data_Prep_Tools import *
import pandas as pd
import logging
import urllib3
import cchardet

urllib3.disable_warnings()

from Prototyping_tool import *

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        link = request.form['url']
        link = link.replace('m.aruodas', 'www.aruodas')
        res = scrape(link)
        return render_template('home.html', value = res['Value'], price = res['Price'])

    return render_template('home.html')
    
def scrape(link):
    logging.debug(f'GOT REQUEST')
    data = [scrape_ad(link=link, nt='Testas', thumb='Testas', save_to_db=False)]
    logging.debug(f'Data collected')
    data = pd.DataFrame(data)
    data = data.to_dict(orient='records')[0]
    price = data['Price']
    data = prep_ml_row(data)
    logging.debug(f'Prepped row')
    data['PRICE PRED'] = predict(data)
    logging.debug(f'Predicted row')
    json_dump = {}
    json_dump['Value'] = str(int(round(data['PRICE PRED']*0.98, -2))) + ' eur'
    json_dump['Price'] = str(price)
    return json_dump

# There will be needed different functions and models for evaluation of ad and evaluation of flat entered by user

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
