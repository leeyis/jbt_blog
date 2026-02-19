from django import forms
from django.conf import settings

from apps.blog.models import Comment


class CommentForm(forms.ModelForm):
    captcha_answer = forms.CharField(
        max_length=16,
        required=True,
        label='验证码',
    )

    class Meta:
        model = Comment
        fields = ['author_name', 'author_email', 'author_website', 'content']

    def clean_content(self):
        content = (self.cleaned_data.get('content') or '').strip()
        min_length = int(getattr(settings, 'COMMENT_MIN_LENGTH', 2))
        max_length = int(getattr(settings, 'COMMENT_MAX_LENGTH', 1000))

        if len(content) < min_length:
            raise forms.ValidationError(f'评论内容至少需要 {min_length} 个字符。')
        if len(content) > max_length:
            raise forms.ValidationError(f'评论内容不能超过 {max_length} 个字符。')

        banned_words = getattr(settings, 'COMMENT_BANNED_WORDS', [])
        lowered_content = content.lower()
        for word in banned_words:
            if word and word.lower() in lowered_content:
                raise forms.ValidationError('评论内容包含敏感词，请修改后再提交。')

        return content
