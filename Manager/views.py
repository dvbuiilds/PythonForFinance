from django.shortcuts import render
from django.views import View
from .functions import find_ticker, create_csv, monthly_trend, daily_trend, criticalpoints, rrratio
import bs4 as bs
import requests
import pickle
from datetime import datetime

# Create your views here.
class Index(View):
    def get(self, request):
        data = Scrap(request)
        request.session['nifty'] = data['nifty']
        request.session['nifty_change'] = data['nifty_change']
        request.session['nifty_pct'] = data['nifty_pct']
        request.session['sensex'] = data['sensex']
        request.session['sensex_change'] = data['sensex_change']
        request.session['sensex_pct'] = data['sensex_pct']
        return render(request, 'index.html')

    def post(self, request):
        data = {}
        name_key = request.POST['search']
        ticker = find_ticker(name_key)

        if ticker:
            pathm, pathd, cmprice, data_m, data_d, ticker = create_csv(ticker)
            request.session['ticker'] = ticker
            l = len('Manager/static/')
            mcsv = pathm[l:]
            dcsv = pathd[l:]
            request.session['mcsv'] = mcsv
            request.session['dcsv'] = dcsv

            data.update({'current_m_price': cmprice})

            Res, Sup, High, Low = criticalpoints(data_m, ticker)

            flag, rr, target, buy_price, stop_loss = rrratio(Res, Sup, High, Low)
            data.update({'n_support': stop_loss, 'n_resistance': target, 'reward_risk': rr, 'flag': flag})

            remark_m = monthly_trend(data_m)
            remark_d = daily_trend(data_d)
            data.update({'monthly_trend': remark_m, 'daily_trend': remark_d})

            print(data)
            return render(request, 'index.html', data)

        else:
            error = 'No Company is listed on that name!'
            data.update({'error': error})
            return render(request, 'index.html', data)


def Scrap(request):
    data = None
    try:
        resp = requests.get('https://economictimes.indiatimes.com/indices/nifty_50_companies')
        soup = bs.BeautifulSoup(resp.text, 'lxml')

        nifty_container = soup.find('div',{'class': 'Div1'})
        nifty_block = nifty_container.find('div',{'id':'headStuff'})
        nifty = nifty_block.find('div', {'id': 'ltp'}).text
        nifty_change = nifty_block.find('div', {'class': 'box todays'})
        nifty_change_no = nifty_change.find('b', {'id':'todaysData'}).text
        components = nifty_change_no.split('(')
        change = float(components[0])

        nifty_pct_change = nifty_change.find('b', {'id': 'todaysData'}).span.text
        print( nifty,nifty_change_no, nifty_pct_change, change )

        resp = requests.get('https://economictimes.indiatimes.com/indices/sensex_30_companies')
        soup = bs.BeautifulSoup(resp.text, 'lxml')

        sensex_container = soup.find('main', {'class' : 'pageHolder'})
        sensex_sec = sensex_container.find('section', {'class': 'fullwidth'})
        sensex = sensex_sec.find('div', {'id': 'ltp'}).text
        sensex_change = sensex_sec('b', {'id': 'todaysData'})[0].text
        sensex_split = sensex_change.split('(')
        sen_change = float(sensex_split[0])
        sensex_pct = '(' + sensex_split[1]
        print(sensex, sen_change, sensex_pct)
        
        data = {'nifty': nifty, 'nifty_change': change, 'nifty_pct': nifty_pct_change, 'sensex': sensex, 
        'sensex_change': sen_change, 'sensex_pct': sensex_pct}

        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%m-%d-%H")
        path = 'picklefiles/'+ timestampStr + '-sennifty.pickle'
        request.session['sennif_path'] = path
        with open(path, 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    except:
        print("Something went wrong")
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%m-%d-%H")
        path = request.session['sennif_path']
        if path:
            with open(path, 'rb') as handle:
                data = pickle.load(handle)
        else:
            path = '03-12-15-sennifty.pickle'
            with open(path, 'rb') as handle:
                data = pickle.load(handle)
 
    return data