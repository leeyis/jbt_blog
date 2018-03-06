from django.shortcuts import render
from apps.blog.models import Article
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.conf import settings


# Create your views here.
def home(request):  # 主页
    posts = Article.objects.all()  # 获取全部的Article对象
    paginator = Paginator(posts, settings.PAGE_NUM)  # 每页显示数量
    page = request.GET.get('page')  # 获取URL中page参数的值
    try:
        post_list = paginator.page(page)
    except PageNotAnInteger:
        post_list = paginator.page(1)
    except EmptyPage:
        post_list = paginator.page(paginator.num_pages)
    return render(request, 'home.html', {'post_list': post_list})


def detail(request, id):
    try:

        post = Article.objects.get(id=str(id))
        post.viewed()  # 更新浏览次数
        tags = post.tags.all()
    except Article.DoesNotExist:
        raise Http404
    return render(request, 'post.html', {'post': post, 'tags': tags})