"""
URL configuration for bitzapp project.

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
from django.urls import path
from core.views import whatsapp_webhook, landing_page, docs_page
from core.lnurl_views import (
    lnurl_callback, 
    lnurl_pay_request, 
    lnurl_withdraw_request, 
    lnurl_withdraw_callback
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing_page'),
    path('docs/', docs_page, name='docs_page'),
    path('webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    
    # LNURL Lightning Address endpoints
    path('.well-known/lnurlp/<str:username>', lnurl_callback, name='lnurl_callback'),
    path('lnurl/callback/<str:username>', lnurl_pay_request, name='lnurl_pay_request'),
    path('lnurl/withdraw/<str:username>', lnurl_withdraw_request, name='lnurl_withdraw_request'),
    path('lnurl/withdraw/<str:username>/callback', lnurl_withdraw_callback, name='lnurl_withdraw_callback'),
]
