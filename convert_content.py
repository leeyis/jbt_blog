import os
import django
import html2text

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbt_blog.settings')
django.setup()

# 导入模型
from apps.blog.models import Article

def convert_html_to_markdown():
    h = html2text.HTML2Text()
    h.body_width = 0  # 不自动换行
    
    try:
        for article in Article.objects.all():
            if article.content:
                # 将 HTML 转换为 Markdown
                markdown_content = h.handle(article.content)
                article.content = markdown_content
                article.save()
                print(f"已转换文章: {article.title}")
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")

if __name__ == '__main__':
    convert_html_to_markdown()
    print("转换完成！")