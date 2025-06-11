from django.shortcuts import render
from apps.blog.models import Article, Category, Tag
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from django.db.models import Count
from django.template.loader import render_to_string
import json

def get_archive_data():
    """获取归档数据，包含每月文章数量"""
    months = Article.objects.filter(status='p', pub_time__isnull=False).datetimes('pub_time', 'month', order='DESC')
    archive_data = []
    for month in months:
        count = Article.objects.filter(
            status='p',
            pub_time__isnull=False,
            pub_time__year=month.year,
            pub_time__month=month.month
        ).count()
        # 创建一个包含日期和数量的字典
        archive_item = {
            'date': month,
            'count': count,
            'year': month.year,
            'month': month.month
        }
        archive_data.append(archive_item)
    return archive_data


def tag_cloud_json(request):
    """为D3.js标签云提供JSON格式数据"""
    tags = Tag.objects.filter(
        article__status='p', 
        article__pub_time__isnull=False
    ).annotate(
        usage_count=Count('article')
    ).order_by('-usage_count').distinct()[:30]  # 增加到30个标签
    
    tag_data = []
    max_count = tags.first().usage_count if tags else 1
    min_count = tags.last().usage_count if tags else 1
    
    for tag in tags:
        # 计算标签的相对大小 (1-5的范围)
        if max_count == min_count:
            size = 3
        else:
            size = 1 + (tag.usage_count - min_count) / (max_count - min_count) * 4
        
        tag_item = {
            'text': tag.name,
            'size': round(size, 1),
            'count': tag.usage_count,
            'url': f'/search_tag/{tag.name}/'  # 标签链接
        }
        tag_data.append(tag_item)
    
    return JsonResponse({'tags': tag_data})


def _get_common_context():
    """获取所有页面都需要的通用上下文数据"""
    archive_data = get_archive_data()  # 先独立获取归档数据
    return {
        'category_list': Category.objects.all(),
        'tag_cloud': Tag.objects.filter(
            article__status='p',
            article__pub_time__isnull=False
        ).annotate(
            usage_count=Count('article')
        ).order_by('-usage_count').distinct()[:20],
        'months': archive_data  # 再将其放入上下文字典
    }

def _handle_pagination(request, posts):
    """处理分页逻辑，同时支持常规请求和AJAX请求"""
    paginator = Paginator(posts, settings.PAGE_NUM)
    page = request.GET.get('page')
    try:
        post_list = paginator.page(page)
    except PageNotAnInteger:
        post_list = paginator.page(1)
    except EmptyPage:
        # 如果是AJAX请求且页面超出范围，返回空内容
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse('')
        post_list = paginator.page(paginator.num_pages)
    return post_list

# Create your views here.
def home(request):  # 主页
    posts = Article.objects.filter(status='p', pub_time__isnull=False)
    post_list = _handle_pagination(request, posts)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # AJAX请求，只返回文章列表部分
        html = render_to_string('post_list_partial.html', {'post_list': post_list})
        # 附加下一页的触发器
        if post_list.has_next():
            html += f'<div id="infinite-scroll-trigger" data-next-page="{post_list.next_page_number}"></div>'
        return HttpResponse(html)

    context = _get_common_context()
    context['post_list'] = post_list
    return render(request, 'home.html', context)


def detail(request, id):
    try:
        post = Article.objects.get(id=str(id))
        post.viewed()  # 更新浏览次数
        tags = post.tags.all()
        next_post = post.next_article()  # 上一篇文章对象
        prev_post = post.prev_article()  # 下一篇文章对象
    except Article.DoesNotExist:
        raise Http404
    
    context = _get_common_context()
    context.update({
        'post': post,
        'tags': tags,
        'next_post': next_post,
        'prev_post': prev_post,
    })
    
    return render(request, 'post.html', context)


def search_category(request, id):
    posts = Article.objects.filter(category_id=str(id), status='p', pub_time__isnull=False)
    
    context = _get_common_context()
    try:
        category = Category.objects.get(id=str(id))
        context['category'] = category
    except Category.DoesNotExist:
        raise Http404("Category not found")
        
    post_list = _handle_pagination(request, posts)
    context['post_list'] = post_list

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # 判断是无限滚动请求还是导航请求
        if request.headers.get('x-infinite-scroll') == 'true':
            return render(request, 'post_list_partial.html', context)
        else:
            return render(request, 'category.html', context)

    return render(request, 'category.html', context)


def search_tag(request, tag):
    posts = Article.objects.filter(tags__name__contains=tag, status='p', pub_time__isnull=False)
    
    context = _get_common_context()
    context['tag'] = tag
    
    post_list = _handle_pagination(request, posts)
    context['post_list'] = post_list

    # For AJAX page loads (main content)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # For AJAX-triggered infinite scroll on the tag page
        if request.headers.get('x-infinite-scroll') == 'true':
            return render(request, 'post_list_partial.html', context)
        # For the initial AJAX load of the tag page
        else:
            return render(request, 'tag.html', context)
    
    # For non-AJAX, direct page loads
    return render(request, 'tag.html', context)


def archives(request, year, month):
    posts = Article.objects.filter(
        status='p',
        pub_time__isnull=False,
        pub_time__year=year,
        pub_time__month=month
    )
    
    context = _get_common_context()
    context['year'] = year
    context['month'] = month
    post_list = _handle_pagination(request, posts)
    context['post_list'] = post_list

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.headers.get('x-infinite-scroll') == 'true':
            return render(request, 'post_list_partial.html', context)
        else:
            return render(request, 'archive.html', context)
        
    return render(request, 'archive.html', context)


def sidebar_preview(request):
    """用于展示侧边栏重构效果的预览视图"""
    context = _get_common_context()
    # 可以在这里添加任何特定于预览页面的额外上下文
    return render(request, 'sidebar_modern_preview.html', context)

