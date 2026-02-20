from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.timezone import now
from mdeditor.widgets import MDEditorWidget

from .models import (
    Article,
    Category,
    Comment,
    CommentNotification,
    OpenSourceProject,
    ProjectMetricSnapshot,
    Tag,
)


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
            'content': MDEditorWidget(),
        }


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'category', 'created_time', 'pub_time', 'status')
    list_filter = ('category', 'status')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_time'

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

        root_comment = comment if comment.parent_id is None else comment.parent

        admin_name = request.user.get_full_name().strip() or request.user.get_username() or '管理员'
        admin_email = request.user.email or getattr(settings, 'COMMENT_ADMIN_EMAIL', '')
        admin_email = admin_email.strip() or 'admin@jbtblog.local'

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


@admin.action(description='立即同步所选项目指标')
def sync_selected_open_source_projects(modeladmin, request, queryset):
    token = (getattr(settings, 'GITHUB_TOKEN', '') or '').strip()
    if not token:
        modeladmin.message_user(
            request,
            'GITHUB_TOKEN 未配置：本次会写入“已跳过”快照，不会从 Github 拉取最新指标。',
            level=messages.WARNING,
        )

    synced_count = 0
    for project in queryset:
        call_command('sync_open_source_metrics', project_slug=project.slug)
        synced_count += 1

    modeladmin.message_user(
        request,
        f'已触发 {synced_count} 个项目的指标同步任务。',
        level=messages.SUCCESS,
    )


class ProjectMetricSnapshotInline(admin.TabularInline):
    model = ProjectMetricSnapshot
    extra = 0
    can_delete = False
    fields = (
        'metric_date',
        'stars',
        'forks',
        'last_commit_at',
        'sync_status',
        'sync_error',
        'created_time',
    )
    readonly_fields = fields
    ordering = ('-metric_date',)


@admin.register(OpenSourceProject)
class OpenSourceProjectAdmin(admin.ModelAdmin):
    change_list_template = 'admin/blog/opensourceproject/change_list.html'
    list_display = (
        'name',
        'sort_order',
        'is_active',
        'is_featured',
        'latest_stars',
        'latest_forks',
        'latest_sync_status',
        'latest_metric_date',
        'sync_now_button',
    )
    list_filter = ('is_active', 'is_featured', 'created_time')
    search_fields = ('name', 'slug', 'github_url', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order', 'is_active', 'is_featured')
    actions = (sync_selected_open_source_projects,)
    inlines = (ProjectMetricSnapshotInline,)

    fieldsets = (
        ('基础信息', {'fields': ('name', 'slug', 'github_url', 'short_description', 'tech_stack')}),
        ('宣传内容', {'fields': ('highlights', 'use_cases')}),
        ('展示控制', {'fields': ('sort_order', 'is_active', 'is_featured')}),
        ('媒体与元信息', {'fields': ('cover_image', 'created_time', 'last_mod_time')}),
    )
    readonly_fields = ('created_time', 'last_mod_time')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'sync-all/',
                self.admin_site.admin_view(self.sync_all_metrics_view),
                name='blog_opensourceproject_sync_all',
            ),
            path(
                '<path:object_id>/sync/',
                self.admin_site.admin_view(self.sync_one_metrics_view),
                name='blog_opensourceproject_sync_one',
            ),
        ]
        return custom_urls + urls

    def sync_all_metrics_view(self, request):
        token = (getattr(settings, 'GITHUB_TOKEN', '') or '').strip()
        if not token:
            self.message_user(
                request,
                'GITHUB_TOKEN 未配置：本次会写入“已跳过”快照，不会从 Github 拉取最新指标。',
                level=messages.WARNING,
            )

        call_command('sync_open_source_metrics')
        self.message_user(request, '已触发全部启用项目的指标同步任务。', level=messages.SUCCESS)
        changelist_url = reverse('admin:blog_opensourceproject_changelist')
        return HttpResponseRedirect(changelist_url)

    def sync_one_metrics_view(self, request, object_id):
        token = (getattr(settings, 'GITHUB_TOKEN', '') or '').strip()
        if not token:
            self.message_user(
                request,
                'GITHUB_TOKEN 未配置：本次会写入“已跳过”快照，不会从 Github 拉取最新指标。',
                level=messages.WARNING,
            )

        project = self.get_object(request, unquote(object_id))
        if project is None:
            self.message_user(request, '项目不存在，无法同步。', level=messages.ERROR)
        else:
            call_command('sync_open_source_metrics', project_slug=project.slug)
            self.message_user(
                request,
                f'已触发项目《{project.name}》的指标同步任务。',
                level=messages.SUCCESS,
            )

        changelist_url = reverse('admin:blog_opensourceproject_changelist')
        return HttpResponseRedirect(changelist_url)

    def _latest_snapshot(self, obj):
        return obj.latest_snapshot

    @admin.display(description='Star')
    def latest_stars(self, obj):
        snapshot = self._latest_snapshot(obj)
        return snapshot.stars if snapshot else 'N/A'

    @admin.display(description='Fork')
    def latest_forks(self, obj):
        snapshot = self._latest_snapshot(obj)
        return snapshot.forks if snapshot else 'N/A'

    @admin.display(description='同步状态')
    def latest_sync_status(self, obj):
        snapshot = self._latest_snapshot(obj)
        return snapshot.get_sync_status_display() if snapshot else 'N/A'

    @admin.display(description='快照日期')
    def latest_metric_date(self, obj):
        snapshot = self._latest_snapshot(obj)
        return snapshot.metric_date if snapshot else 'N/A'

    @admin.display(description='同步操作')
    def sync_now_button(self, obj):
        url = reverse('admin:blog_opensourceproject_sync_one', args=[obj.pk])
        return format_html('<a class="button" href="{}">立即同步</a>', url)


@admin.register(ProjectMetricSnapshot)
class ProjectMetricSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'project',
        'metric_date',
        'stars',
        'forks',
        'last_commit_at',
        'sync_status',
    )
    list_filter = ('sync_status', 'metric_date')
    search_fields = ('project__name', 'project__slug', 'sync_error')
    readonly_fields = ('created_time', 'last_mod_time')


# 自定义管理界面设置
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', '金笔头博客管理后台')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', '金笔头博客')
admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', '欢迎访问后台管理')
