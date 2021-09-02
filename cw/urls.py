from django.urls import path
from .views import Homepage, News_List, News_Crawl, News_Page, News_Simliar, News_Detail

app_name = 'homepage'

urlpatterns = [
    path('', Homepage, name = 'Homepage'),
    path('crawling/', News_Crawl, name= 'crawling'),
    path('list/', News_List, name ='list'),
    path('list2/', News_Page, name = 'list2'),
    path('simliar/', News_Simliar, name = 'simliar'),
    path('detail/', News_Detail, name = 'detail')
]
