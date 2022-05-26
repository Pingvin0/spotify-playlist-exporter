from django.urls import path
from front import views


app_name = 'front'


urlpatterns = [
    path('', views.index, name='index'),
    path('authorize/', views.authorize, name='authorize'),
    path('spotify_callback/', views.spotify_callback, name='spotify_callback'),
    path('download_export/<str:key>/', views.download_export, name='download_export')
]