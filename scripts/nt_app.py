from flask import Flask, redirect, url_for, render_template, request, session, json
import logging
import urllib3
import re
from prod import get_prediction
urllib3.disable_warnings()

app = Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')

@app.route('/', methods=['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        url = request.form['url']
        rent, price, real = get_prediction(url)
        if real > 10000:
            roi = round((rent*12) / real * 100, 2)
            return render_template('index.html',\
                value = f'Paskaičiuota vertė: {price} €, paskaičiuota nuomos kaina: {rent} €, kaina skelbime: {real} €, numatoma metinė grąža: {roi} %')
        return render_template('index.html',\
            value = f'Paskaičiuota vertė: {price} €, paskaičiuota nuomos kaina: {rent} €, kaina skelbime: {real} €')
    return render_template('index.html', value = 'Laukiama nuorodos..')

@app.errorhandler(500)
def page_not_found(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500



if __name__ == '__main__':
    app.run(debug=False, threaded=True)

