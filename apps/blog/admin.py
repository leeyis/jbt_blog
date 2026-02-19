from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.utils.timezone import now

from .models import Article, Category, Comment, CommentNotification, Tag
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


@admin.action(description='审核通过所选评论')
def approve_comments(modeladmin, request, queryset):
    for comment in queryset:
        comment.status = Comment.STATUS_APPROVED
        comment.approved_time = now()
        comment.save()


@admin.action(description='拒绝所选评论')
def reject_comments(modeladmin, request, queryset):
    for comment in queryset:
        comment.status = Comment.STATUS_REJECTED
        comment.save()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    change_form_template = 'admin/blog/comment/change_form.html'
    list_display = ('author_name', 'article', 'parent', 'status', 'created_time', 'approved_time')
    list_filter = ('status', 'created_time')
    search_fields = ('author_name', 'author_email', 'content', 'article__title')
    readonly_fields = ('created_time', 'last_mod_time', 'approved_time', 'ip_hash')
    date_hierarchy = 'created_time'
    actions = (approve_comments, reject_comments)

    fieldsets = (
        ('基础信息', {'fields': ('article', 'parent', 'status')}),
        ('评论内容', {'fields': ('author_name', 'author_email', 'author_website', 'content')}),
        ('审计信息', {'fields': ('ip_hash', 'created_time', 'last_mod_time', 'approved_time')}),
    )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.method == 'POST' and '_reply_and_approve' in request.POST:
            comment = self.get_object(request, unquote(object_id))
            if comment is None:
                self.message_user(request, '评论不存在，无法执行快捷回复。', level=messages.ERROR)
                return HttpResponseRedirect(request.path)
            self._handle_admin_quick_reply(request, comment)
            return HttpResponseRedirect(request.path)
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def _handle_admin_quick_reply(self, request, comment):
        reply_content = (request.POST.get('admin_reply_content') or '').strip()
        if not reply_content:
            self.message_user(request, '回复内容不能为空。', level=messages.ERROR)
            return

        # 保持仅一级回复：不管当前评论是否为回复，都挂在根评论下。
        root_comment = comment if comment.parent_id is None else comment.parent

        admin_name = request.user.get_full_name().strip() or request.user.get_username() or '管理员'
        admin_email = request.user.email or getattr(settings, 'COMMENT_ADMIN_EMAIL', '')
        admin_email = admin_email.strip() or 'admin@jbtblog.local'

        # 按你的验收需求：后台直接回复时，原评论自动审核通过。
        comments_to_approve = [comment]
        if root_comment != comment and root_comment.status != Comment.STATUS_APPROVED:
            comments_to_approve.append(root_comment)

        for item in comments_to_approve:
            if item.status != Comment.STATUS_APPROVED:
                item.status = Comment.STATUS_APPROVED
                item.approved_time = now()
                item.save()

        prefixed_content = reply_content
        if root_comment != comment:
            prefixed_content = f'@{comment.author_name} {reply_content}'

        reply = Comment.objects.create(
            article=root_comment.article,
            parent=root_comment,
            author_name=admin_name,
            author_email=admin_email,
            content=prefixed_content,
            status=Comment.STATUS_APPROVED,
        )

        self.message_user(
            request,
            f'已完成快捷回复：原评论已通过，管理员回复（#{reply.id}）已发布。',
            level=messages.SUCCESS,
        )


@admin.register(CommentNotification)
class CommentNotificationAdmin(admin.ModelAdmin):
    list_display = ('comment', 'notification_type', 'target_email', 'status', 'retry_count', 'created_time', 'sent_time')
    list_filter = ('notification_type', 'status', 'created_time')
    search_fields = ('target_email', 'comment__content', 'comment__article__title')
    readonly_fields = (
        'comment',
        'notification_type',
        'target_email',
        'status',
        'retry_count',
        'last_error',
        'next_retry_at',
        'created_time',
        'sent_time',
    )

# 自定义管理界面设置
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', '金笔头博客管理后台')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', '金笔头博客')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', '欢迎访问后台管理')
