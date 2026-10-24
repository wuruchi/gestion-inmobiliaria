"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('base.urls')),
]

# urlpatterns += static(settings.STATIC_URL, document_root=str(settings.STATIC_ROOT))
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=str(settings.MEDIA_ROOT))
urlpatterns += static(settings.IMG_URL, document_root=str(settings.IMG_ROOT))
urlpatterns += static(settings.JS_URL, document_root=str(settings.JS_ROOT))
urlpatterns += static(settings.CSS_URL, document_root=str(settings.CSS_ROOT))

urlpatterns += [
    path('', TemplateView.as_view(template_name='index.html')),
]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# if settings.JS_ROOT: urlpatterns += static(settings.JS_URL, document_root=settings.JS_ROOT)
# if settings.CSS_ROOT: urlpatterns += static(settings.CSS_URL, document_root=settings.CSS_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

