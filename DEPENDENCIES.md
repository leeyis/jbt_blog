# 项目依赖说明

## 核心依赖

### Django>=5.2.2
- **用途**: 项目的核心Web框架
- **使用位置**: 整个项目
- **说明**: 已升级到Django 5.x版本，享受最新功能和安全更新

### django-mdeditor>=0.1.20
- **用途**: Markdown富文本编辑器
- **使用位置**: 
  - `settings.py` - INSTALLED_APPS和MDEDITOR_CONFIGS配置
  - `models.py` - Article.content字段使用MDTextField
  - `urls.py` - 包含mdeditor的URL配置
- **说明**: 替代了原来的django-summernote编辑器

### bleach>=6.2.0
- **用途**: HTML内容清理和安全过滤
- **使用位置**: django-mdeditor的依赖，用于清理用户输入的HTML
- **说明**: 防止XSS攻击，确保内容安全

## 界面美化依赖

### django-admin-interface>=0.30.0
- **用途**: Django管理界面主题美化
- **使用位置**: `settings.py` - INSTALLED_APPS中的'admin_interface'
- **说明**: 提供现代化的管理界面，替代了django-jet

### django-colorfield>=0.14.0
- **用途**: 颜色字段支持（admin-interface的依赖）
- **使用位置**: `settings.py` - INSTALLED_APPS中的'colorfield'
- **说明**: 为管理界面提供颜色选择器功能

## Markdown处理依赖

### markdown>=3.8
- **用途**: 将Markdown文本转换为HTML
- **使用位置**: `templatetags/markdown_extras.py` - markdown过滤器
- **说明**: 支持扩展功能如代码高亮、表格、目录等

### Pygments>=2.19.1
- **用途**: 代码语法高亮
- **使用位置**: markdown扩展中的codehilite
- **说明**: 为代码块提供语法高亮显示

## 工具依赖

### html2text>=2025.4.15
- **用途**: 将HTML内容转换为Markdown格式
- **使用位置**: `convert_content.py` - 数据迁移脚本
- **说明**: 用于将旧的HTML内容批量转换为Markdown

### Pillow>=11.2.1
- **用途**: 图片处理库
- **使用位置**: mdeditor上传图片功能
- **说明**: Django处理图片文件的必需依赖

### python-slugify>=8.0.4
- **用途**: 将字符串转换为URL友好的格式
- **使用位置**: django-mdeditor的依赖
- **说明**: 用于生成文件名和URL标识符

## 核心框架依赖

### asgiref>=3.8.1
- **用途**: ASGI（异步服务器网关接口）支持
- **使用位置**: Django核心依赖
- **说明**: Django的异步支持基础库

### sqlparse>=0.5.3
- **用途**: SQL解析器
- **使用位置**: Django ORM
- **说明**: 用于SQL语句的解析和格式化

## 已移除的依赖

### ❌ django-jet-reboot==1.3.10
- **移除原因**: 与django-admin-interface冲突，功能重复
- **替代方案**: django-admin-interface
- **建议**: 运行 `pip uninstall django-jet-reboot` 卸载

### ❌ django-jet==1.0.7
- **移除原因**: 已被django-admin-interface替代
- **替代方案**: django-admin-interface

### ❌ django-summernote==0.8.8.6
- **移除原因**: 已被django-mdeditor替代
- **替代方案**: django-mdeditor

## 清理命令

```bash
# 卸载不需要的包
pip uninstall django-jet-reboot django-jet django-summernote -y

# 安装/更新依赖
pip install -r requirements.txt
```

## 完整安装命令

```bash
# 从零开始安装所有依赖
pip install Django>=5.2.2
pip install django-mdeditor>=0.1.20
pip install bleach>=6.2.0
pip install django-admin-interface>=0.30.0
pip install django-colorfield>=0.14.0
pip install markdown>=3.8
pip install Pygments>=2.19.1
pip install html2text>=2025.4.15
pip install Pillow>=11.2.1
pip install python-slugify>=8.0.4
pip install asgiref>=3.8.1
pip install sqlparse>=0.5.3
```

## 版本兼容性

- Python 3.8+
- Django 5.x
- 所有依赖都是最新稳定版本，确保安全性和性能

## 配置清理

项目已清理了以下不再需要的配置：
- ✅ 移除了JET_THEMES配置
- ✅ 移除了JET_SIDE_MENU配置
- ✅ 移除了SUMMERNOTE_CONFIG配置
- ✅ 保留了MDEDITOR_CONFIGS配置 