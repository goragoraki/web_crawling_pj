from django.shortcuts import render, redirect
from .forms import HomeForm
from .models import News
import requests
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from numpy import dot, empty
from numpy.linalg import norm
import numpy as np
from konlpy.tag import Okt
import pandas as pd
from queue import PriorityQueue
import json
from numpy import dot
from numpy.linalg import norm
import numpy as np
from konlpy.tag import Okt
import  pandas as pd
import csv
import os
from django import forms
# Create your views here.
def cos_sim(a,b):
    if norm(a)*norm(b)!=0:
        return dot(a,b)/(norm(a)*norm(b))
    else:
        return 0

def make_matrix(feats, list_data):
    freq_list = []
    for feat in feats:
        freq = 0
        for word in list_data:
            if feat == word:
                freq+=1
        freq_list.append(freq)
    return freq_list


def Homepage(request):
    return render(request, 'home.html')

def News_Crawl(request):
    news_num = int(30)
    ## create url and parsing (naver kbs news)
    news_url = 'https://search.naver.com/search.naver?where=news&query=kbs&sm=tab_clk.jou&sort=0&photo=0&field=0&pd=0&ds=&de=&docid=&related=0&mynews=0&office_type=&office_section_code=&news_office_checked=&nso=so%3Ar%2Cp%3Aall%2Ca%3Aall&is_sug_officeid=1'
    req = requests.get(news_url)
    soup = BeautifulSoup(req.text,'html.parser')
    ##
    news_titles = {}
    news_urls = {}
    idx = 0
    cur_page = 1
    print('crawling')
    while idx < news_num:
        ## find news tags
        table = soup.find('ul',{'class' : 'list_news'})
        li_list = table.find_all('li',{'id' : re.compile('sp_nws.*')})
        area_list = [li.find('div',{'class' : 'news_area'}) for li in li_list]
        a_list = [area.find('a',{'class' : 'news_tit'}) for area in area_list]

        ## save title and main text address
        for n in a_list[:min(len(a_list),news_num-idx)]:
            news_titles[idx] = n.get('title')
            news_urls[idx]= n.get('href')
            idx += 1

        cur_page +=1

        ## find next news page tags
        pages = soup.find('div',{'class' : 'sc_page_inner'})
        next_page_url = [p for p in pages.find_all('a') if p.text == str(cur_page)][0].get('href')

        req = requests.get('https://search.naver.com/search.naver' + next_page_url)
        soup = BeautifulSoup(req.text, 'html.parser')

    ## main_text crawling (kbs)
    news_main_text ={}
    idx = 0
    for url in news_urls.values():
        req = requests.get(url)
        req.encoding = None
        soup = BeautifulSoup(req.text, 'html.parser')
        news_main_text[idx] = soup.find('div',{'id' : 'cont_newstext'}).text.strip()
        idx += 1
    print('crawling complete')

    #save news
    f = open('csv/news_list.csv', 'w', newline='')
    wr = csv.writer(f)
    for n in range(0,len(news_titles)):
        wr.writerow([news_titles[n],news_main_text[n]])
    f.close()

    print('saved news')
    
    redirect('homepage:Homepage')


def News_List(request):
    workpath =os.path.dirname(os.path.abspath(__file__))

    f = open(os.path.join(workpath, 'news_list.csv'),'r')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    news_titles={}
    news_main_text={}
    for n in range(0,len(data_rdr)):
        news_titles[n] = data_rdr[n][0]
        news_main_text[n] = data_rdr[n][1]
    f.close()
    
    #단어 추출 , 형태소 추출
    print('extracting words ...')
    news_simliar = []
    tempSimliar = []
    temp_arr =[]
    t_arr=[]
    voc = []

    okt = Okt()
    for n in news_main_text.values():
        tempSimliar.extend(okt.nouns(n))
        t_arr.append(okt.nouns(n))
        voc.extend(okt.morphs(n))

    ## 중복 제거, 불용어 제거
    feats = list(set(tempSimliar))
    voc = list(set(voc))
    stop_words = ['이제', '인물', '동안', '단번', '사이', '스무', '순간','과연','마저','만큼','누구','주변','소유자','오늘']
    feats = list(filter(lambda x:len(x)>1 and x not in stop_words, feats))

    ## 명사 매트릭스 생성
    for n in t_arr:
        temp_arr.append(np.array(make_matrix(feats,n)))

    ## nan -> 0으로 치환
    dataSet = pd.DataFrame(temp_arr)
    dataSet = dataSet.fillna(0)
    temp_arr = dataSet.values.tolist()
    
## 
    if request.method == "POST":
        k_w = HomeForm(request.POST)
        if k_w.is_valid():
            k_ = k_w.cleaned_data['key_word']
    
    user_f_word = k_
    user_f_idx = 0
    for n in feats:
        if n == user_f_word:
            break
        else:
            user_f_idx +=1

    que = PriorityQueue()
    for n in range(0, len(temp_arr)):
        que.put((-temp_arr[n][user_f_idx],n))
    
    s_title = []
    s_text = []
    idx_num = 1
    user_command = -1
    temp_idx= []
    for n in range(1, que.qsize()+1): 
        idx_num = que.get()[1]
        temp_idx.append(idx_num)
        s_title.append(news_titles[idx_num])
        s_text.append(news_main_text[idx_num])
        print('%d. %s'%(n, news_titles[idx_num]))

    f = open(os.path.join(workpath, 'news_list2.csv'), 'w', newline='')
    wr = csv.writer(f)
    for n in temp_idx:
        wr.writerow([news_titles[n],news_main_text[n]])
    f.close()
    context = {
        "news_title" : s_title,
        "news_main_text" : s_text,
        "k_w" : k_,
    }
    return render(request, "news_list.html", context)
    