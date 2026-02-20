import hashlib
import random
import time
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Prefetch, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST

from apps.blog.forms import CommentForm
from apps.blog.models import (
    Article,
    Category,
    Comment,
    CommentNotification,
    OpenSourceProject,
    ProjectMetricSnapshot,
    Tag,
)


CAPTCHA_SESSION_KEY = 'comment_captcha'

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


def _build_comment_captcha():
    left = random.randint(1, 9)
    right = random.randint(1, 9)
    if random.choice([True, False]):
        question = f'{left} + {right} = ?'
        answer = left + right
    else:
        larger, smaller = max(left, right), min(left, right)
        question = f'{larger} - {smaller} = ?'
        answer = larger - smaller
    return question, str(answer)


def _ensure_comment_captcha(request, force_refresh=False):
    ttl = int(getattr(settings, 'COMMENT_CAPTCHA_TTL_SECONDS', 600))
    now_ts = int(time.time())
    captcha_data = request.session.get(CAPTCHA_SESSION_KEY)

    is_expired = (
        not captcha_data
        or captcha_data.get('created_at', 0) + ttl < now_ts
    )
    if force_refresh or is_expired:
        question, answer = _build_comment_captcha()
        captcha_data = {
            'question': question,
            'answer': answer,
            'created_at': now_ts,
        }
        request.session[CAPTCHA_SESSION_KEY] = captcha_data
        request.session.modified = True
    return captcha_data


def _validate_comment_captcha(request, provided_answer):
    captcha_data = _ensure_comment_captcha(request)
    normalized_answer = (provided_answer or '').strip()
    if normalized_answer != str(captcha_data.get('answer', '')).strip():
        return False
    _ensure_comment_captcha(request, force_refresh=True)
    return True


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _hash_ip(raw_ip):
    if not raw_ip:
        return ''
    payload = f"{settings.SECRET_KEY}:{raw_ip}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _is_comment_rate_limited(author_email, ip_hash):
    window_seconds = int(getattr(settings, 'COMMENT_RATE_LIMIT_WINDOW_SECONDS', 300))
    max_attempts = int(getattr(settings, 'COMMENT_RATE_LIMIT_MAX_ATTEMPTS', 3))
    start_time = now() - timedelta(seconds=window_seconds)

    if not author_email and not ip_hash:
        return False

    recent_comments = Comment.objects.filter(created_time__gte=start_time)
    limiter_filter = Q()
    if author_email:
        limiter_filter |= Q(author_email__iexact=author_email)
    if ip_hash:
        limiter_filter |= Q(ip_hash=ip_hash)
    return recent_comments.filter(limiter_filter).count() >= max_attempts


def _comment_redirect_url(article_id):
    return f"{reverse('detail', kwargs={'id': article_id})}#comments"


def _submit_comment(request, article, parent_comment=None):
    redirect_url = _comment_redirect_url(article.id)
    form = CommentForm(request.POST)
    captcha_answer = request.POST.get('captcha_answer', '')

    if not _validate_comment_captcha(request, captcha_answer):
        messages.error(request, '验证码错误，请重新输入后再提交。')
        return redirect(redirect_url)

    author_email = (request.POST.get('author_email') or '').strip().lower()
    client_ip_hash = _hash_ip(_get_client_ip(request))
    if _is_comment_rate_limited(author_email, client_ip_hash):
        messages.error(request, '评论过于频繁，请稍后再试。')
        return redirect(redirect_url)

    if not form.is_valid():
        for field_errors in form.errors.values():
            if field_errors:
                messages.error(request, field_errors[0])
        return redirect(redirect_url)

    comment = form.save(commit=False)
    comment.article = article
    comment.parent = parent_comment
    comment.ip_hash = client_ip_hash
    comment.status = Comment.STATUS_PENDING
    try:
        comment.full_clean()
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect(redirect_url)

    comment.save()
    CommentNotification.enqueue_new_comment(comment)
    messages.success(request, '评论提交成功，审核通过后将显示在页面中。')
    return redirect(redirect_url)


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

    approved_replies_queryset = Comment.objects.filter(
        status=Comment.STATUS_APPROVED
    ).order_by('created_time')
    approved_comments = post.comments.filter(
        status=Comment.STATUS_APPROVED,
        parent__isnull=True,
    ).order_by('created_time').prefetch_related(
        Prefetch('replies', queryset=approved_replies_queryset, to_attr='approved_replies')
    )
    captcha_data = _ensure_comment_captcha(request)

    context = _get_common_context()
    context.update({
        'post': post,
        'tags': tags,
        'next_post': next_post,
        'prev_post': prev_post,
        'approved_comments': approved_comments,
        'comment_form': CommentForm(),
        'captcha_question': captcha_data['question'],
    })

    return render(request, 'post.html', context)


def opensource(request):
    projects = list(
        OpenSourceProject.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'metric_snapshots',
                queryset=ProjectMetricSnapshot.objects.order_by('-metric_date'),
            )
        )
    )

    featured_medals = {
        1: '🥇',
        2: '🥈',
        3: '🥉',
    }
    featured_rank = 0

    for project in projects:
        snapshots = list(project.metric_snapshots.all())
        project.latest_snapshot_cache = snapshots[0] if snapshots else None
        project.featured_rank = None
        project.featured_medal = ''
        if project.is_featured:
            featured_rank += 1
            project.featured_rank = featured_rank
            project.featured_medal = featured_medals.get(featured_rank, '')

    context = _get_common_context()
    context['project_list'] = projects
    return render(request, 'opensource.html', context)


def opensource_detail(request, slug):
    project = get_object_or_404(
        OpenSourceProject.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'metric_snapshots',
                queryset=ProjectMetricSnapshot.objects.order_by('-metric_date'),
            )
        ),
        slug=slug,
    )
    snapshots = list(project.metric_snapshots.all())
    latest_snapshot = snapshots[0] if snapshots else None

    context = _get_common_context()
    context['project'] = project
    context['latest_snapshot'] = latest_snapshot
    return render(request, 'opensource_detail.html', context)


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


@require_POST
def comment_create(request, id):
    article = get_object_or_404(Article, id=id, status='p')
    return _submit_comment(request, article)


@require_POST
def comment_reply(request, id, comment_id):
    article = get_object_or_404(Article, id=id, status='p')
    parent_comment = get_object_or_404(
        Comment,
        id=comment_id,
        article=article,
        parent__isnull=True,
        status=Comment.STATUS_APPROVED,
    )
    return _submit_comment(request, article, parent_comment=parent_comment)
