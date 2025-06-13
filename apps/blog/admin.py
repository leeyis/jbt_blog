from django.contrib import admin
from .models import Article, Category, Tag
from django.conf import settings
from django import forms
from mdeditor.widgets import MDEditorWidget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/popup_fix.css',)
        }

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/popup_fix.css',)
        }


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            'content': MDEditorWidget()
        }


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'category', 'created_time', 'pub_time', 'status')  # 列表显示的字段
    list_filter = ('category', 'status')  # 过滤器
    search_fields = ('title', 'content')  # 搜索字段
    date_hierarchy = 'created_time'  # 日期筛选
    
    # 在管理界面显示的字段顺序
    fields = (
        'title', 
        'content',
        'status',
        'category',
        'tags',
        'pub_time',
    )
    
    class Media:
        js = ('js/mdeditor-enhance.js', 'js/article_admin_setup.js',)
        css = {
            'all': ('css/mdeditor-enhance.css', 'css/article_admin_style.css',)
        }

# 自定义管理界面设置
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', '金笔头博客管理后台')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', '金笔头博客')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', '欢迎访问后台管理')