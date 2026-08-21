"""
URL configuration for assentag project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from temp.views import add_index
from django.conf import settings
from django.conf.urls.static import static


from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
     path('complaint/',include('complaint.url')),
     path('feedback/',include('feedback.url')),
     path('image/',include('image.url')),
     path('login/',include('login.url')),
     path('register/',include('register.url')),
     path('index/',include('temp.url')),
     path('', add_index, name='root_index'),
     path('generate/',include('generate.url')),
     path('verify/',include('varify.url')),
     path('favicon.ico', RedirectView.as_view(url='/static/assets/logo.svg', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
