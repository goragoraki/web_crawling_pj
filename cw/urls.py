from django.urls import path
from .views import Homepage, News_List, News_Crawl

app_name = 'homepage'

urlpatterns = [
    path('', Homepage, name = 'Homepage'),
    path('crawling/', News_Crawl, name= 'crawling'),
    path('list/', News_List, name ='list'),
]
