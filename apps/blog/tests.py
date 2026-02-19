from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import Article, Category, Comment, CommentNotification


def _set_comment_captcha(session, answer='2', question='1 + 1 = ?'):
    session['comment_captcha'] = {
        'answer': str(answer),
        'question': question,
        'created_at': int(timezone.now().timestamp()),
    }
    session.save()


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
