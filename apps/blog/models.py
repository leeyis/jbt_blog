from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from mdeditor.fields import MDTextField


# Create your models here.
class Tag(models.Model):
    name = models.CharField(verbose_name='标签名', max_length=64)
    created_time = models.DateTimeField(verbose_name='创建时间', default=now)
    last_mod_time = models.DateTimeField(verbose_name='修改时间', default=now)

    # 使对象在后台显示更友好
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = '标签名称'  # 指定后台显示模型名称
        verbose_name_plural = '标签列表'  # 指定后台显示模型复数名称
        db_table = "tag"  # 数据库表名


class Category(models.Model):
    name = models.CharField(verbose_name='类别名称', max_length=64)
    created_time = models.DateTimeField(verbose_name='创建时间', default=now)
    last_mod_time = models.DateTimeField(verbose_name='修改时间', default=now)

    class Meta:
        ordering = ['name']
        verbose_name = "类别名称"
        verbose_name_plural = '分类列表'
        db_table = "category"  # 数据库表名

    # 使对象在后台显示更友好
    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_CHOICES = (
        ('d', '草稿'),
        ('p', '发表'),
    )
    title = models.CharField(verbose_name='标题', max_length=100)
    content = MDTextField(verbose_name='正文', blank=True, null=True)  # 替换 TextField
    status = models.CharField(verbose_name='状态', max_length=1, choices=STATUS_CHOICES, default='p')
    views = models.PositiveIntegerField(verbose_name='浏览量', default=0)
    created_time = models.DateTimeField(verbose_name='创建时间', default=now)
    pub_time = models.DateTimeField(verbose_name='发布时间', blank=True, null=True)
    last_mod_time = models.DateTimeField(verbose_name='修改时间', default=now)
    category = models.ForeignKey(Category, verbose_name='分类', on_delete=models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField(Tag, verbose_name='标签集合', blank=True)

    # 使对象在后台显示更友好
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """重写save方法，自动处理发布时间"""
        if self.status == 'p':  # 如果状态为发表
            if not self.pub_time:  # 且发布时间为空
                self.pub_time = now()  # 设置当前时间为发布时间
        else:  # 如果状态为草稿
            self.pub_time = None  # 清空发布时间
        
        # 更新修改时间
        self.last_mod_time = now()
        
        super().save(*args, **kwargs)

    # 更新浏览量
    def viewed(self):
        self.views += 1
        self.save(update_fields=['views'])

    # 下一篇
    def next_article(self):  # 发布时间比当前文章早的文章，按发布时间降序取第一篇（时间轴上的下一篇）
        return Article.objects.filter(
            pub_time__lt=self.pub_time, 
            status='p', 
            pub_time__isnull=False
        ).order_by('-pub_time').first()

    # 前一篇  
    def prev_article(self):  # 发布时间比当前文章晚的文章，按发布时间升序取第一篇（时间轴上的上一篇）
        return Article.objects.filter(
            pub_time__gt=self.pub_time, 
            status='p', 
            pub_time__isnull=False
        ).order_by('pub_time').first()

    class Meta:
        ordering = ['-pub_time']  # 按文章创建日期降序
        verbose_name = '文章'  # 指定后台显示模型名称
        verbose_name_plural = '文章列表'  # 指定后台显示模型复数名称
        db_table = 'article'  # 数据库表名
        get_latest_by = 'created_time'


class Comment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = (
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已拒绝'),
    )

    article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE, verbose_name='文章')
    parent = models.ForeignKey(
        'self',
        related_name='replies',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='父评论'
    )
    author_name = models.CharField(max_length=64, verbose_name='昵称')
    author_email = models.EmailField(verbose_name='邮箱')
    author_website = models.URLField(blank=True, verbose_name='个人网站')
    content = models.TextField(verbose_name='评论内容')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name='审核状态')
    ip_hash = models.CharField(max_length=64, blank=True, verbose_name='IP摘要')
    created_time = models.DateTimeField(default=now, verbose_name='创建时间')
    last_mod_time = models.DateTimeField(default=now, verbose_name='修改时间')
    approved_time = models.DateTimeField(blank=True, null=True, verbose_name='审核通过时间')

    class Meta:
        ordering = ['created_time']
        verbose_name = '评论'
        verbose_name_plural = '评论列表'
        db_table = 'comment'
        indexes = [
            models.Index(fields=['article', 'status']),
            models.Index(fields=['created_time']),
        ]

    def __str__(self):
        return f'{self.author_name}: {self.content[:20]}'

    def clean(self):
        if self.parent_id:
            if self.parent.article_id != self.article_id:
                raise ValidationError('回复评论必须属于同一篇文章。')
            if self.parent.parent_id:
                raise ValidationError('当前仅支持一级回复。')

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Comment.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        self.last_mod_time = now()
        if self.status == self.STATUS_APPROVED and not self.approved_time:
            self.approved_time = now()
        elif self.status != self.STATUS_APPROVED:
            self.approved_time = None

        self.full_clean()
        super().save(*args, **kwargs)

        if self.parent_id and self.status == self.STATUS_APPROVED and previous_status != self.STATUS_APPROVED:
            CommentNotification.enqueue_reply_notification(self)


class CommentNotification(models.Model):
    TYPE_NEW_COMMENT = 'new_comment'
    TYPE_REPLY = 'reply'
    TYPE_CHOICES = (
        (TYPE_NEW_COMMENT, '新评论通知'),
        (TYPE_REPLY, '回复通知'),
    )

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_DISABLED = 'disabled'
    STATUS_CHOICES = (
        (STATUS_PENDING, '待发送'),
        (STATUS_SENT, '已发送'),
        (STATUS_FAILED, '发送失败'),
        (STATUS_DISABLED, '已禁用'),
    )

    comment = models.ForeignKey(Comment, related_name='notifications', on_delete=models.CASCADE, verbose_name='关联评论')
    notification_type = models.CharField(max_length=24, choices=TYPE_CHOICES, verbose_name='通知类型')
    target_email = models.EmailField(blank=True, verbose_name='目标邮箱')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name='状态')
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name='重试次数')
    last_error = models.TextField(blank=True, verbose_name='最近错误')
    next_retry_at = models.DateTimeField(blank=True, null=True, verbose_name='下次重试时间')
    sent_time = models.DateTimeField(blank=True, null=True, verbose_name='发送时间')
    created_time = models.DateTimeField(default=now, verbose_name='创建时间')

    class Meta:
        ordering = ['created_time']
        verbose_name = '评论通知任务'
        verbose_name_plural = '评论通知任务'
        db_table = 'comment_notification'
        indexes = [
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['created_time']),
        ]

    def __str__(self):
        return f'{self.get_notification_type_display()} -> {self.target_email or "N/A"}'

    @classmethod
    def enqueue_new_comment(cls, comment):
        target_email = getattr(settings, 'COMMENT_ADMIN_EMAIL', '').strip()
        if not target_email:
            return cls.objects.create(
                comment=comment,
                notification_type=cls.TYPE_NEW_COMMENT,
                target_email='',
                status=cls.STATUS_DISABLED,
            )
        return cls.objects.create(
            comment=comment,
            notification_type=cls.TYPE_NEW_COMMENT,
            target_email=target_email,
            status=cls.STATUS_PENDING,
        )

    @classmethod
    def enqueue_reply_notification(cls, comment):
        if not comment.parent_id or not comment.parent.author_email:
            return None

        target_email = comment.parent.author_email.strip()
        if target_email.lower() == comment.author_email.lower():
            return None

        return cls.objects.create(
            comment=comment,
            notification_type=cls.TYPE_REPLY,
            target_email=target_email,
            status=cls.STATUS_PENDING,
        )





