from django.core import paginator
from django.shortcuts import render, redirect
from .forms import HomeForm, InputForm
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
from django.core.paginator import Paginator
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
    news_num = int(50)
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

    workpath =os.path.dirname(os.path.abspath(__file__))
    #save news
    f = open(os.path.join(workpath,'news_list.csv'), 'w', newline='',encoding='UTF-8')
    wr = csv.writer(f)
    for n in range(0,len(news_titles)):
        wr.writerow([news_titles[n], news_main_text[n]])
    f.close()

    print('saved news')
    
    redirect('homepage:Homepage')


def News_List(request):
    workpath =os.path.dirname(os.path.abspath(__file__))

    f = open(os.path.join(workpath, 'news_list.csv'),'r',encoding='UTF-8')
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
    temp_idx= []
    for n in range(1, que.qsize()+1): 
        idx_num = que.get()[1]
        temp_idx.append(idx_num)
        s_title.append(news_titles[idx_num])
        s_text.append(news_main_text[idx_num])

    f = open(os.path.join(workpath, 'news_list2.csv'), 'w', newline='',encoding='UTF-8')
    wr = csv.writer(f)
    for n in temp_idx:
        wr.writerow([news_titles[n],news_main_text[n]])
    f.close()

    return redirect('homepage:list2')

def News_Page(request):
    workpath =os.path.dirname(os.path.abspath(__file__))

    f = open(os.path.join(workpath, 'news_list2.csv'),'r',encoding='UTF-8')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    news_titles=[]
    for n in range(0,len(data_rdr)):
        news_titles.append(data_rdr[n][0])
    f.close()

    page = request.GET.get('page','1')

    paginator = Paginator(news_titles,20)
    page_obj = paginator.get_page(page)

    context = {
        "news_title" : news_titles,
        "board_list" : page_obj,
    }
    return render(request, "news_list.html", context)

def News_Simliar(request):
    
    workpath =os.path.dirname(os.path.abspath(__file__))

    f = open(os.path.join(workpath, 'news_list2.csv'),'r',encoding='UTF-8')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    news_titles={}
    news_main_text={}
    for n in range(0,len(data_rdr)):
        news_titles[n] = data_rdr[n][0]
        news_main_text[n] = data_rdr[n][1]
    f.close()

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
    
    if request.method == "POST":
        k_w = InputForm(request.POST)
        if k_w.is_valid():
            user_command = k_w.cleaned_data['key_word']
            print(user_command)

    news_index = int(user_command)-1

    t_idx =0
    for n in temp_arr:
        c1 = round(cos_sim(temp_arr[news_index],n),4)
        news_simliar.append([c1, t_idx])
        t_idx+=1

    news_simliar.sort(key=lambda x:x[0])
    news_simliar.reverse()

    print("Simliar news")
    f = open(os.path.join(workpath, 'news_similar.csv'), 'w', newline='',encoding='UTF-8')
    wr = csv.writer(f)
    for n in range(1,21):
        print(n,news_titles[news_simliar[n][1]], end='')
        print(" Similarity : %0.2f%%" %(news_simliar[n][0]*100))
        wr.writerow([news_titles[news_simliar[n][1]],news_simliar[n][0]*100])
    f.close()


    ## top 5 word
    que = PriorityQueue()
    m_word_idx=[]
    cnt=0
    t_w = []
    for n in temp_arr[news_index]:
        que.put((-n,cnt))
        cnt+=1  
    print("top words")
    for n in range(1,6):
        t_w.append(feats[que.get()[1]])

    ##세부사항 저장
    f = open(os.path.join(workpath, 'news_detail.csv'), 'w', newline='',encoding='UTF-8')
    wr = csv.writer(f)
    wr.writerow([news_titles[news_index],news_main_text[news_index]])
    f.close()

    ## top5 word 저장
    f = open(os.path.join(workpath, 'top_word.csv'), 'w', newline='',encoding='UTF-8')
    wr = csv.writer(f)
    for n in range(0,5):
        wr.writerow(t_w[n])
    f.close()

    return redirect('homepage:detail')

def News_Detail(request):

    workpath =os.path.dirname(os.path.abspath(__file__))

    ## 뉴스 내용
    f = open(os.path.join(workpath, 'news_detail.csv'),'r',encoding='UTF-8')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    n_titles=data_rdr[0][0]
    n_main=data_rdr[0][1] 
    f.close()

    ##유사 뉴스
    f = open(os.path.join(workpath, 'news_similar.csv'),'r',encoding='UTF-8')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    s_titles=[]
    s_sim=[]
    for n in range(0,len(data_rdr)):
        s_titles.append(data_rdr[n][0])
        s_sim.append(data_rdr[n][1]) 
    f.close()

    f = open(os.path.join(workpath, 'top_word.csv'),'r',encoding='UTF-8')
    rdr =csv.reader(f)
    data_rdr = list(rdr)
    top_w = []
    for n in data_rdr:
        top_w.append(n)
    f.close()

    s_list = zip(s_titles,s_sim)
    context ={
        'n_t' : n_titles,
        'n_m' : n_main,
        's_l' : s_list,
        't_w' : top_w,
    }

    return render(request, "news_detail.html", context)