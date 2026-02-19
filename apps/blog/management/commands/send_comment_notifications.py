from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import now

from apps.blog.models import CommentNotification


class Command(BaseCommand):
    help = '发送评论通知邮件（异步队列消费命令）'
    RETRY_BACKOFF_MINUTES = [1, 5, 30]

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help='单次最多处理的通知任务数量')

    def handle(self, *args, **options):
        limit = options['limit']
        current_time = now()
        max_retry = int(getattr(settings, 'COMMENT_NOTIFICATION_MAX_RETRIES', 3))

        notifications = CommentNotification.objects.filter(
            status__in=[CommentNotification.STATUS_PENDING, CommentNotification.STATUS_FAILED]
        ).filter(
            Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=current_time)
        ).order_by('created_time')[:limit]

        sent_count = 0
        failed_count = 0
        skipped_count = 0

        for notification in notifications:
            if notification.retry_count >= max_retry:
                notification.status = CommentNotification.STATUS_FAILED
                notification.next_retry_at = None
                notification.save(update_fields=['status', 'next_retry_at'])
                skipped_count += 1
                continue

            if not notification.target_email:
                notification.status = CommentNotification.STATUS_DISABLED
                notification.last_error = '目标邮箱为空，任务已禁用'
                notification.save(update_fields=['status', 'last_error'])
                skipped_count += 1
                continue

            subject, body = self._build_email(notification)
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[notification.target_email],
                    fail_silently=False,
                )
                notification.status = CommentNotification.STATUS_SENT
                notification.sent_time = now()
                notification.last_error = ''
                notification.next_retry_at = None
                notification.save(update_fields=['status', 'sent_time', 'last_error', 'next_retry_at'])
                sent_count += 1
            except Exception as exc:  # pragma: no cover - 覆盖在测试中通过mock触发
                notification.retry_count += 1
                notification.status = CommentNotification.STATUS_FAILED
                notification.last_error = str(exc)[:500]
                if notification.retry_count < max_retry:
                    backoff_index = min(notification.retry_count - 1, len(self.RETRY_BACKOFF_MINUTES) - 1)
                    notification.next_retry_at = now() + timedelta(minutes=self.RETRY_BACKOFF_MINUTES[backoff_index])
                else:
                    notification.next_retry_at = None
                notification.save(update_fields=['retry_count', 'status', 'last_error', 'next_retry_at'])
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Comment notifications processed: sent={sent_count}, failed={failed_count}, skipped={skipped_count}'
            )
        )

    def _build_email(self, notification):
        comment = notification.comment
        article = comment.article
        base_url = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
        article_path = reverse('detail', kwargs={'id': article.id})
        article_url = f'{base_url}{article_path}' if base_url else article_path

        if notification.notification_type == CommentNotification.TYPE_REPLY:
            subject = f'[站点回复通知] 你在《{article.title}》的评论有新回复'
            body = (
                f'你好，\n\n'
                f'你在《{article.title}》下的评论收到新回复。\n'
                f'回复者：{comment.author_name}\n'
                f'回复内容：\n{comment.content}\n\n'
                f'查看文章：{article_url}\n'
            )
        else:
            subject = f'[站点评论通知] 《{article.title}》收到新评论'
            body = (
                f'管理员你好，\n\n'
                f'文章《{article.title}》收到一条新评论，当前状态为待审核。\n'
                f'评论者：{comment.author_name} ({comment.author_email})\n'
                f'评论内容：\n{comment.content}\n\n'
                f'文章地址：{article_url}\n'
            )
        return subject, body
