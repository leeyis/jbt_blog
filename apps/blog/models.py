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







