
from django.shortcuts import render, redirect
from django.views import View

import datetime as dt
import pandas as pd
import pandas_datareader.data as web
import bs4 as bs
#import pickle
import requests
import os
import numpy as np


def find_ticker(keyword):
    sample = pd.read_csv('Manager/files/coname&tickers.csv')
    sample = pd.DataFrame(sample)
    conames = sample['Company Names'].to_list()
    tickers = sample['Tickers'].to_list()
    
    flag = 0
    if ' ' in keyword:
        for tmp in conames:
            if keyword.lower() in tmp.lower():
                tick = tickers[conames.index(tmp)]
                flag = 1
        tick = tick

    else:
        for tmp in tickers:
            if keyword.upper() in tmp:
                tick = tmp
                flag = 1
    if flag == 1:
        return tick
    else:
        return None

def create_csv(ticker):
    start = dt.datetime(2010, 1, 1)
    end = dt.datetime.now()
    start_d = dt.datetime(2020, 5, 1)

    try:
        print('try stmt...')
        data_m = web.get_data_yahoo(ticker, start, end, interval = 'm')
        data_d = web.get_data_yahoo(ticker, start_d, end, interval = 'd')
        
        path = 'Manager/static/Manager/'
        pathm = path + ticker + '_m.csv'
        pathd = path + ticker + '_d.csv'

        data_m.to_csv(pathm)
        data_d.to_csv(pathd)
    except:
        print('except stmt...')
        ticker = 'ICICIBANK.NS'
        path = 'Manager/static/Manager/'
        pathm = path + ticker + '_m.csv'
        pathd = path + ticker + '_d.csv'


    data_m = pd.read_csv(pathm)
    data_d = pd.read_csv(pathd)

    data_d['10 D M.A.'] = data_d['Close'].rolling(window=10).mean()
    data_m['10 M M.A.'] = data_m['Close'].rolling(window=10).mean()

    cmprice = data_d['Close'][len(data_d) - 1]

    return pathm, pathd, cmprice, data_m, data_d, ticker

def criticalpoints(data_m, ticker):

    df = pd.DataFrame(data_m)

    #Resistance and Support
    Close = df['Close'].to_list()
    High = df['High'].to_list()
    Low = df['Low'].to_list()
    ma = df['10 M M.A.'].to_list()

    temp = []
    Sup = []
    Res = []

    Sup.append(Low[0])

    #Calculation into lists.

    i = 9
    while( i < len(Close)-1 ):
        while ((i < len(Close)-1) and (Close[i] >  ma[i])):
            temp.append(High[i])
            #print(High[i])
            i += 1
            
        if len(temp) != 0 :
            Res.append(max(temp))
        
        temp.clear()
        
        while ((i < len(Close)-1) and (Close[i] <= ma[i])):
            temp.append(Low[i])
            #print(Low[i])
            i += 1
        
        if len(temp) != 0:
            Sup.append(min(temp))
        
        temp.clear()

    #filtering of Resistance
    leng = len(Res)
    for i in range(leng):
        dict = {}

    for t in Res:
        if ( abs((Res[i]-t)*100/Res[i]) < 4):
            dict.update({t: Res.index(t)})

    tmp = dict.keys()
    l = len(tmp)
    avg = sum(tmp)/l

    for x in Res:
        if x in tmp:
            Res[dict[x]] = avg

    print(Res)
    temp = []
    for t in Res:
        if t not in temp:
            temp.append(t)
    Res = temp
    print(Res)

    #filtering the supports
    leng = len(Sup)
    for i in range(leng):
        dict = {}

    for t in Sup:
        if ( abs((Sup[i]-t)*100/Sup[i]) < 4):
            dict.update({t: Sup.index(t)})

    tmp = dict.keys()
    l = len(tmp)
    avg = sum(tmp)/l

    for x in Sup:
        if x in tmp:
            Sup[dict[x]] = avg

    print(Sup)
    temp = []
    for t in Sup:
        if t not in temp:
            temp.append(t)
    Sup = temp
    print(Sup)
    return Res, Sup, High, Low

#Nearest support and Resistance.
def closest_criticals(cric_arr, bprice):

    lo1 = max(cric_arr)-bprice
    lo2 = bprice-min(cric_arr)
    req1 = req2 = bprice
    for tmp in cric_arr:
        if bprice < tmp:
            if ((tmp - bprice) < lo1):
                lo1 = tmp - bprice
                req1 = tmp
        
        elif bprice >= tmp:
            if ((bprice - tmp) < lo2):
                lo2 = tmp - bprice
                req2 = tmp
    
    return req1, req2

#Reward Risk Ratio.
def rrratio(Res, Sup, High, Low):

    l1 = len(High) - 1
    buy_price = (High[l1]+Low[l1])/2
    target, stop_loss = closest_criticals(Res + Sup, buy_price)#nearest support to buy price
    #target = #nearest resistance level
    reward = target - buy_price
    risk = buy_price - stop_loss
    flag = 0
    try:
        rr = reward / risk
    except:
        rr = 'Very High'
        flag = 2

    if (type(rr) == float):
        remark = 'The Reward Risk Ratio is ' + str(rr)
        if rr >= 2:
            flag = 1
        else:
            flag = 0
    return flag, rr, target, buy_price, stop_loss

def monthly_trend(data_m):
    #Monthly trend detection.
    ic = 0    #increase count
    dc = 0    #decrease count

    df = pd.DataFrame(data_m)

    Close = df['Close'].to_list()
    l = len(Close)
    for i in range(l-8, l-1):
        if Close[i-1]>Close[i]:
            dc += 1
        elif Close[i-1]<Close[i]:
            ic += 1

    remark = 'The Monthly historical data suggests that '
    if abs(ic - dc) <= 1:
        remark += "the current trend is neutral"

    elif ic>dc:
        remark += "the stock is in Uptrend!"

    elif dc>ic:
        remark += "the stock is in Downtrend!"
    return remark

def daily_trend(data_d):
    #daily Trend detection
    ic = 0    #increase count
    dc = 0    #decrease count

    df = pd.DataFrame(data_d)

    Close = df['Close'].to_list()
    l = len(Close)
    for i in range(l-18,l-1):
        if Close[i-1]>Close[i]:
            dc += 1
        elif Close[i-1]<Close[i]:
            ic += 1
    remark = 'The Daily historical data suggests that '
    if abs(ic - dc) <= 1:
        remark += "the current trend is neutral"

    elif ic>dc:
        remark += "the stock is in Uptrend!"

    elif dc>ic:
        remark += "the stock is in Downtrend!"
    return remark
