"""jbt_blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, re_path
from apps.blog import views
from django.conf.urls import include
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('manage/', admin.site.urls),
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('sidebar_preview/', views.sidebar_preview, name='sidebar_preview'),
    path('articles/<int:id>/', views.detail, name='detail'),
    path('category/<int:id>/', views.search_category, name='category_menu'),
    path('tag/<str:tag>/', views.search_tag, name='search_tag'),
    path('archives/<str:year>/<str:month>', views.archives, name='archives'),
    path('api/tagcloud/', views.tag_cloud_json, name='tag_cloud_json'),  # 标签云JSON API
    path('mdeditor/', include('mdeditor.urls')),  # 替换 summernote
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]