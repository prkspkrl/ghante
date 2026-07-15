from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('popular-projects/', views.popular_projects, name='popular_projects'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('service/<str:skill>/', views.service_detail, name='service_detail'),
    path('project/<str:slug>/', views.project_detail, name='project_detail'),
    path('search/', views.search, name='search'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
]
