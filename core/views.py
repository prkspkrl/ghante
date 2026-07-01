from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')


def services(request):
    return render(request, 'core/services.html')


def popular_projects(request):
    return render(request, 'core/popular_projects.html')


def how_it_works(request):
    return render(request, 'core/how_it_works.html')
