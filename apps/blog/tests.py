import json
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import (
    Article,
    Category,
    Comment,
    CommentNotification,
    OpenSourceProject,
    ProjectMetricSnapshot,
)


def _set_comment_captcha(session, answer='2', question='1 + 1 = ?'):
    session['comment_captcha'] = {
        'answer': str(answer),
        'question': question,
        'created_at': int(timezone.now().timestamp()),
    }
    session.save()


class _MockHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


@override_settings(
    COMMENT_RATE_LIMIT_WINDOW_SECONDS=300,
    COMMENT_RATE_LIMIT_MAX_ATTEMPTS=2,
    COMMENT_MIN_LENGTH=2,
    COMMENT_MAX_LENGTH=500,
    COMMENT_BANNED_WORDS=['spam-word'],
    COMMENT_ADMIN_EMAIL='admin@example.com',
)
class TestCommentMVP(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='测试分类')
        self.article = Article.objects.create(
            title='测试文章',
            content='hello world',
            status='p',
            category=self.category,
            pub_time=timezone.now(),
        )

    def test_comment_defaults_to_pending(self):
        comment = Comment.objects.create(
            article=self.article,
            author_name='Alice',
            author_email='alice@example.com',
            content='这是一条待审核评论',
        )
        self.assertEqual(comment.status, Comment.STATUS_PENDING)

    def test_reply_depth_is_limited_to_one_level(self):
        root = Comment.objects.create(
            article=self.article,
            author_name='Root',
            author_email='root@example.com',
            content='root comment',
        )
        reply = Comment.objects.create(
            article=self.article,
            parent=root,
            author_name='Reply1',
            author_email='reply1@example.com',
            content='first level reply',
        )
        nested_reply = Comment(
            article=self.article,
            parent=reply,
            author_name='Reply2',
            author_email='reply2@example.com',
            content='second level reply',
        )
        with self.assertRaises(ValidationError):
            nested_reply.full_clean()

    def test_approved_reply_will_enqueue_reply_notification(self):
        root = Comment.objects.create(
            article=self.article,
            author_name='Root',
            author_email='root@example.com',
            content='root comment',
            status=Comment.STATUS_APPROVED,
        )
        reply = Comment.objects.create(
            article=self.article,
            parent=root,
            author_name='Reply',
            author_email='reply@example.com',
            content='pending reply',
            status=Comment.STATUS_PENDING,
        )
        self.assertFalse(
            CommentNotification.objects.filter(
                comment=reply,
                notification_type=CommentNotification.TYPE_REPLY,
            ).exists()
        )

        reply.status = Comment.STATUS_APPROVED
        reply.save()

        self.assertTrue(
            CommentNotification.objects.filter(
                comment=reply,
                notification_type=CommentNotification.TYPE_REPLY,
                target_email='root@example.com',
            ).exists()
        )

    def test_create_comment_requires_valid_captcha(self):
        session = self.client.session
        _set_comment_captcha(session, answer='8', question='5 + 3 = ?')

        url = reverse('comment_create', kwargs={'id': self.article.id})
        response = self.client.post(
            url,
            data={
                'author_name': 'Tom',
                'author_email': 'tom@example.com',
                'content': 'valid comment content',
                'captcha_answer': '9',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)

    def test_create_comment_success_and_admin_notification_enqueued(self):
        session = self.client.session
        _set_comment_captcha(session)

        url = reverse('comment_create', kwargs={'id': self.article.id})
        response = self.client.post(
            url,
            data={
                'author_name': 'Tom',
                'author_email': 'tom@example.com',
                'content': 'this is a valid first comment',
                'captcha_answer': '2',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        created = Comment.objects.first()
        self.assertEqual(created.status, Comment.STATUS_PENDING)
        self.assertTrue(
            CommentNotification.objects.filter(
                comment=created,
                notification_type=CommentNotification.TYPE_NEW_COMMENT,
                status=CommentNotification.STATUS_PENDING,
                target_email='admin@example.com',
            ).exists()
        )

    def test_create_comment_respects_rate_limit(self):
        url = reverse('comment_create', kwargs={'id': self.article.id})

        for index in range(2):
            session = self.client.session
            _set_comment_captcha(session)
            self.client.post(
                url,
                data={
                    'author_name': f'Tom{index}',
                    'author_email': 'tom@example.com',
                    'content': f'comment no {index}',
                    'captcha_answer': '2',
                },
            )

        session = self.client.session
        _set_comment_captcha(session)
        self.client.post(
            url,
            data={
                'author_name': 'Tom3',
                'author_email': 'tom@example.com',
                'content': 'third comment should be blocked',
                'captcha_answer': '2',
            },
            follow=True,
        )

        self.assertEqual(Comment.objects.count(), 2)

    def test_detail_page_only_displays_approved_comments(self):
        Comment.objects.create(
            article=self.article,
            author_name='Pending',
            author_email='p@example.com',
            content='pending content',
            status=Comment.STATUS_PENDING,
        )
        approved = Comment.objects.create(
            article=self.article,
            author_name='Approved',
            author_email='a@example.com',
            content='approved content',
            status=Comment.STATUS_APPROVED,
        )

        response = self.client.get(reverse('detail', kwargs={'id': self.article.id}))
        self.assertEqual(response.status_code, 200)
        approved_comments = response.context['approved_comments']
        self.assertEqual(list(approved_comments), [approved])

    def test_reply_submission_uses_parent_comment(self):
        parent = Comment.objects.create(
            article=self.article,
            author_name='Parent',
            author_email='parent@example.com',
            content='parent comment',
            status=Comment.STATUS_APPROVED,
        )

        session = self.client.session
        _set_comment_captcha(session)

        url = reverse(
            'comment_reply',
            kwargs={'id': self.article.id, 'comment_id': parent.id},
        )
        self.client.post(
            url,
            data={
                'author_name': 'Child',
                'author_email': 'child@example.com',
                'content': 'reply comment',
                'captcha_answer': '2',
            },
            follow=True,
        )

        self.assertEqual(Comment.objects.count(), 2)
        child = Comment.objects.exclude(id=parent.id).first()
        self.assertEqual(child.parent_id, parent.id)
        self.assertEqual(child.status, Comment.STATUS_PENDING)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com',
    SITE_BASE_URL='https://example.com',
)
class TestCommentNotificationCommand(TestCase):
    def setUp(self):
        category = Category.objects.create(name='测试分类')
        self.article = Article.objects.create(
            title='测试文章',
            content='hello world',
            status='p',
            category=category,
            pub_time=timezone.now(),
        )
        self.comment = Comment.objects.create(
            article=self.article,
            author_name='Alice',
            author_email='alice@example.com',
            content='test notification',
            status=Comment.STATUS_APPROVED,
        )

    def test_send_comment_notifications_command_marks_sent(self):
        notification = CommentNotification.objects.create(
            comment=self.comment,
            notification_type=CommentNotification.TYPE_NEW_COMMENT,
            target_email='admin@example.com',
            status=CommentNotification.STATUS_PENDING,
        )

        call_command('send_comment_notifications', limit=20)

        notification.refresh_from_db()
        self.assertEqual(notification.status, CommentNotification.STATUS_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('测试文章', mail.outbox[0].subject)

    @patch('apps.blog.management.commands.send_comment_notifications.send_mail')
    def test_send_comment_notifications_command_retries_on_failure(self, mocked_send_mail):
        mocked_send_mail.side_effect = RuntimeError('smtp down')

        notification = CommentNotification.objects.create(
            comment=self.comment,
            notification_type=CommentNotification.TYPE_NEW_COMMENT,
            target_email='admin@example.com',
            status=CommentNotification.STATUS_PENDING,
        )

        call_command('send_comment_notifications', limit=20)

        notification.refresh_from_db()
        self.assertEqual(notification.status, CommentNotification.STATUS_FAILED)
        self.assertEqual(notification.retry_count, 1)
        self.assertIsNotNone(notification.next_retry_at)


@override_settings(COMMENT_ADMIN_EMAIL='admin@example.com')
class TestCommentAdminQuickReply(TestCase):
    def setUp(self):
        category = Category.objects.create(name='测试分类')
        self.article = Article.objects.create(
            title='测试文章',
            content='hello world',
            status='p',
            category=category,
            pub_time=timezone.now(),
        )
        self.pending_comment = Comment.objects.create(
            article=self.article,
            author_name='访客',
            author_email='visitor@example.com',
            content='请问这个功能如何扩展？',
            status=Comment.STATUS_PENDING,
        )
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Admin@123456',
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_reply_and_auto_approve_from_admin_page(self):
        change_url = reverse('admin:blog_comment_change', args=[self.pending_comment.id])
        response = self.client.post(
            change_url,
            data={
                '_reply_and_approve': '1',
                'admin_reply_content': '后台已处理，后续会继续优化。',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.pending_comment.refresh_from_db()
        self.assertEqual(self.pending_comment.status, Comment.STATUS_APPROVED)

        admin_reply = Comment.objects.filter(
            article=self.article,
            parent=self.pending_comment,
            status=Comment.STATUS_APPROVED,
            author_name='admin',
        ).first()
        self.assertIsNotNone(admin_reply)
        self.assertIn('后续会继续优化', admin_reply.content)

        self.assertTrue(
            CommentNotification.objects.filter(
                comment=admin_reply,
                notification_type=CommentNotification.TYPE_REPLY,
                target_email='visitor@example.com',
                status=CommentNotification.STATUS_PENDING,
            ).exists()
        )


class TestOpenSourceAdminSyncEntry(TestCase):
    def setUp(self):
        self.project = OpenSourceProject.objects.create(
            name='Admin Sync Project',
            slug='admin-sync-project',
            github_url='https://github.com/example/admin-sync-project',
            short_description='admin sync desc',
            highlights='亮点A\n亮点B',
            use_cases='场景A\n场景B',
            is_active=True,
        )
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username='admin_sync',
            email='admin_sync@example.com',
            password='Admin@123456',
        )
        self.client.force_login(self.admin_user)

    def test_open_source_admin_changelist_contains_sync_entries(self):
        response = self.client.get(reverse('admin:blog_opensourceproject_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '同步全部项目指标')
        self.assertContains(response, '立即同步')

    @patch('apps.blog.admin.call_command')
    def test_open_source_admin_sync_all_view_triggers_command(self, mocked_call_command):
        response = self.client.get(reverse('admin:blog_opensourceproject_sync_all'), follow=True)
        self.assertEqual(response.status_code, 200)
        mocked_call_command.assert_called_once_with('sync_open_source_metrics')

    @patch('apps.blog.admin.call_command')
    def test_open_source_admin_sync_one_view_triggers_command(self, mocked_call_command):
        response = self.client.get(
            reverse('admin:blog_opensourceproject_sync_one', args=[self.project.id]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        mocked_call_command.assert_called_once_with(
            'sync_open_source_metrics',
            project_slug=self.project.slug,
        )


class TestOpenSourceProjectModels(TestCase):
    def test_open_source_project_ordering_by_sort_order(self):
        OpenSourceProject.objects.create(
            name='Project B',
            slug='project-b',
            github_url='https://github.com/example/project-b',
            short_description='project b desc',
            highlights='亮点1\n亮点2',
            use_cases='场景1\n场景2',
            sort_order=20,
        )
        OpenSourceProject.objects.create(
            name='Project A',
            slug='project-a',
            github_url='https://github.com/example/project-a',
            short_description='project a desc',
            highlights='亮点1\n亮点2',
            use_cases='场景1\n场景2',
            sort_order=10,
        )

        slugs = list(OpenSourceProject.objects.values_list('slug', flat=True))
        self.assertEqual(slugs, ['project-a', 'project-b'])

    def test_highlights_and_use_cases_are_required(self):
        project = OpenSourceProject(
            name='Project Required',
            slug='project-required',
            github_url='https://github.com/example/project-required',
            short_description='required desc',
            highlights='',
            use_cases='',
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_metric_snapshot_unique_per_day(self):
        project = OpenSourceProject.objects.create(
            name='Project Metrics',
            slug='project-metrics',
            github_url='https://github.com/example/project-metrics',
            short_description='metrics desc',
            highlights='亮点1',
            use_cases='场景1',
        )
        metric_date = timezone.localdate()

        ProjectMetricSnapshot.objects.create(
            project=project,
            metric_date=metric_date,
            stars=10,
            forks=3,
        )
        with self.assertRaises(IntegrityError):
            ProjectMetricSnapshot.objects.create(
                project=project,
                metric_date=metric_date,
                stars=12,
                forks=4,
            )


class TestOpenSourceViews(TestCase):
    def setUp(self):
        self.active_project = OpenSourceProject.objects.create(
            name='Active Project',
            slug='active-project',
            github_url='https://github.com/example/active-project',
            short_description='active desc',
            highlights='亮点A\n亮点B',
            use_cases='场景A\n场景B',
            sort_order=1,
            is_active=True,
            is_featured=True,
        )
        self.inactive_project = OpenSourceProject.objects.create(
            name='Inactive Project',
            slug='inactive-project',
            github_url='https://github.com/example/inactive-project',
            short_description='inactive desc',
            highlights='亮点A',
            use_cases='场景A',
            sort_order=2,
            is_active=False,
        )
        ProjectMetricSnapshot.objects.create(
            project=self.active_project,
            metric_date=timezone.localdate(),
            stars=123,
            forks=45,
            sync_status=ProjectMetricSnapshot.SYNC_SUCCESS,
        )

    def test_open_source_wall_and_detail_page_returns_200(self):
        wall_response = self.client.get(reverse('opensource'))
        detail_response = self.client.get(
            reverse('opensource_detail', kwargs={'slug': self.active_project.slug})
        )
        self.assertEqual(wall_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_open_source_detail_unknown_slug_returns_404(self):
        response = self.client.get(reverse('opensource_detail', kwargs={'slug': 'not-exists'}))
        self.assertEqual(response.status_code, 404)

    def test_open_source_wall_only_displays_active_projects(self):
        response = self.client.get(reverse('opensource'))
        self.assertContains(response, 'Active Project')
        self.assertNotContains(response, 'Inactive Project')

    def test_open_source_wall_renders_na_when_metrics_missing(self):
        OpenSourceProject.objects.create(
            name='No Metric Project',
            slug='no-metric-project',
            github_url='https://github.com/example/no-metric-project',
            short_description='no metric desc',
            highlights='亮点A',
            use_cases='场景A',
            sort_order=3,
            is_active=True,
        )
        response = self.client.get(reverse('opensource'))
        self.assertContains(response, 'N/A')

    def test_sidebar_github_link_redirects_to_open_source_page(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'title="Github"')
        self.assertContains(response, 'href="/opensource/"')

    def test_open_source_wall_featured_badge_uses_icon(self):
        response = self.client.get(reverse('opensource'))
        self.assertContains(response, '🥇')
        self.assertContains(response, '主推项目第1名')
        self.assertNotContains(response, 'fa-rocket')

    def test_open_source_metrics_icons_render_hover_tips(self):
        wall_response = self.client.get(reverse('opensource'))
        detail_response = self.client.get(
            reverse('opensource_detail', kwargs={'slug': self.active_project.slug})
        )
        self.assertContains(wall_response, 'title="Star 数"')
        self.assertContains(wall_response, 'title="Fork 数"')
        self.assertContains(wall_response, 'title="最近提交时间"')
        self.assertContains(detail_response, 'title="Star 数"')
        self.assertContains(detail_response, 'title="Fork 数"')
        self.assertContains(detail_response, 'title="最近提交时间"')

    def test_open_source_detail_github_button_has_no_leading_icon(self):
        response = self.client.get(
            reverse('opensource_detail', kwargs={'slug': self.active_project.slug})
        )
        self.assertContains(response, '前往 Github')
        self.assertNotContains(response, '<i class="fa fa-github"></i> 前往 Github')


class TestSyncOpenSourceMetricsCommand(TestCase):
    def setUp(self):
        self.project = OpenSourceProject.objects.create(
            name='Sync Project',
            slug='sync-project',
            github_url='https://github.com/example/sync-project',
            short_description='sync desc',
            highlights='亮点A',
            use_cases='场景A',
        )

    @override_settings(GITHUB_TOKEN='dummy-token')
    @patch('apps.blog.management.commands.sync_open_source_metrics.urlopen')
    def test_sync_command_success_writes_snapshot(self, mocked_urlopen):
        mocked_urlopen.return_value = _MockHTTPResponse(
            {
                'stargazers_count': 88,
                'forks_count': 20,
                'pushed_at': '2026-02-20T01:02:03Z',
            }
        )
        call_command('sync_open_source_metrics')

        snapshot = ProjectMetricSnapshot.objects.get(
            project=self.project, metric_date=timezone.localdate()
        )
        self.assertEqual(snapshot.stars, 88)
        self.assertEqual(snapshot.forks, 20)
        self.assertEqual(snapshot.sync_status, ProjectMetricSnapshot.SYNC_SUCCESS)
        self.assertEqual(snapshot.sync_error, '')

    @override_settings(GITHUB_TOKEN='')
    def test_sync_command_skips_when_token_missing(self):
        call_command('sync_open_source_metrics')

        snapshot = ProjectMetricSnapshot.objects.get(
            project=self.project, metric_date=timezone.localdate()
        )
        self.assertEqual(snapshot.sync_status, ProjectMetricSnapshot.SYNC_SKIPPED)
        self.assertIn('GITHUB_TOKEN', snapshot.sync_error)

    @override_settings(GITHUB_TOKEN='dummy-token')
    @patch('apps.blog.management.commands.sync_open_source_metrics.urlopen')
    def test_sync_command_fallbacks_to_latest_snapshot_on_error(self, mocked_urlopen):
        ProjectMetricSnapshot.objects.create(
            project=self.project,
            metric_date=timezone.localdate() - timedelta(days=1),
            stars=77,
            forks=12,
            sync_status=ProjectMetricSnapshot.SYNC_SUCCESS,
        )
        mocked_urlopen.side_effect = RuntimeError('api error')

        call_command('sync_open_source_metrics')

        snapshot = ProjectMetricSnapshot.objects.get(
            project=self.project, metric_date=timezone.localdate()
        )
        self.assertEqual(snapshot.stars, 77)
        self.assertEqual(snapshot.forks, 12)
        self.assertEqual(snapshot.sync_status, ProjectMetricSnapshot.SYNC_FAILED)
        self.assertIn('api error', snapshot.sync_error)


class TestSeedOpenSourceProjectsCommand(TestCase):
    sample_slugs = [
        'jbt-blog',
        'ip-proxy-pool',
        'moerduo',
        'antvis-mcp-sse',
        'md2html',
        'message-board',
    ]

    def test_seed_command_creates_curated_projects_and_snapshots(self):
        call_command('seed_open_source_projects')

        self.assertEqual(OpenSourceProject.objects.count(), len(self.sample_slugs))
        self.assertEqual(
            ProjectMetricSnapshot.objects.filter(metric_date=timezone.localdate()).count(),
            len(self.sample_slugs),
        )

        for slug in self.sample_slugs:
            project = OpenSourceProject.objects.get(slug=slug)
            self.assertTrue(project.highlights.strip())
            self.assertTrue(project.use_cases.strip())

        jbt_blog_project = OpenSourceProject.objects.get(slug='jbt-blog')
        jbt_blog_snapshot = ProjectMetricSnapshot.objects.get(
            project=jbt_blog_project,
            metric_date=timezone.localdate(),
        )
        self.assertEqual(jbt_blog_snapshot.stars, 146)
        self.assertEqual(jbt_blog_snapshot.forks, 51)
        self.assertIsNotNone(jbt_blog_snapshot.last_commit_at)
        self.assertEqual(jbt_blog_snapshot.last_commit_at.date().isoformat(), '2025-06-16')

    def test_seed_command_is_idempotent_and_updates_existing_project(self):
        OpenSourceProject.objects.create(
            name='旧版项目',
            slug='jbt-blog',
            github_url='https://github.com/leeyis/jbt_blog',
            short_description='old desc',
            highlights='旧亮点',
            use_cases='旧场景',
            sort_order=999,
            is_featured=False,
        )

        call_command('seed_open_source_projects')
        call_command('seed_open_source_projects')

        self.assertEqual(OpenSourceProject.objects.count(), len(self.sample_slugs))
        project = OpenSourceProject.objects.get(slug='jbt-blog')
        self.assertEqual(project.name, 'jbt_blog')
        self.assertEqual(project.short_description, '现代化 Django 博客系统，支持 Markdown 与可视化管理后台。')
        self.assertEqual(project.sort_order, 10)
        self.assertTrue(project.is_featured)
