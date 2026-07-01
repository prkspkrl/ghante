from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('popular-projects/', views.popular_projects, name='popular_projects'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]
