from django.contrib import admin
from .models import Article, Category, Tag

admin.site.register(Category)
admin.site.register(Tag)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
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