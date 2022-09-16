from flask import Flask, redirect, url_for, render_template, request, session, json
import logging
import urllib3
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
        url = 'https://' + 'www.aruodas.lt/' + '1-' + url.split('1-')[1][0:7]
        prediction, price = get_prediction(url)
        return render_template('index.html',\
             value = f'Paskaičiuota vertė: {prediction} €, skelbime nurodyta kaina: {price} €')
    return render_template('index.html', value = 'Laukiama nuorodos..')

@app.errorhandler(500)
def page_not_found(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=False, threaded=True)

