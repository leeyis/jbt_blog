import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """
    将Markdown文本转换为HTML
    """
    if not text:
        return ''
    
    # 配置Markdown扩展
    extensions = [
        'markdown.extensions.extra',      # 支持表格、脚注等
        'markdown.extensions.codehilite', # 代码高亮
        'markdown.extensions.toc',        # 目录
        'markdown.extensions.nl2br',      # 换行转<br>
    ]
    
    # 配置代码高亮
    extension_configs = {
        'markdown.extensions.codehilite': {
            'css_class': 'highlight',
            'use_pygments': True,
        }
    }
    
    # 转换Markdown为HTML
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs
    )
    
    html = md.convert(text)
    return mark_safe(html)

@register.filter(name='markdown_truncate')
def markdown_truncate(text, length=300):
    """
    截取Markdown文本的纯文本部分用于摘要
    """
    if not text:
        return ''
    
    # 转换为HTML后再去除标签
    html = markdown_format(text)
    from django.utils.html import strip_tags
    plain_text = strip_tags(html)
    
    # 截取指定长度
    if len(plain_text) > length:
        return plain_text[:length] + '...'
    return plain_text