#!/usr/bin/env python3
"""
依赖检查脚本
检查项目中实际使用的Python包是否都已正确安装
"""

import sys
import importlib
import subprocess


def check_package(package_name, import_name=None):
    """检查包是否可以导入"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} - 已安装并可导入")
        return True
    except ImportError:
        print(f"❌ {package_name} - 未安装或导入失败")
        return False


def get_installed_packages():
    """获取已安装的包列表"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"获取包列表失败: {e}")
        return ""


def main():
    print("=" * 50)
    print("金笔头博客项目依赖检查")
    print("=" * 50)
    
    # 核心依赖检查
    required_packages = [
        ('Django', 'django'),
        ('django-mdeditor', 'mdeditor'),
        ('django-admin-interface', 'admin_interface'),
        ('django-colorfield', 'colorfield'),
        ('markdown', 'markdown'),
        ('Pygments', 'pygments'),
        ('asgiref', 'asgiref'),
        ('sqlparse', 'sqlparse'),
    ]
    
    print("\n📦 检查必需依赖:")
    all_good = True
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            all_good = False
    
    # 可选依赖检查
    optional_packages = [
        ('html2text', 'html2text'),
        ('Pillow', 'PIL'),
        ('bleach', 'bleach'),
        ('python-slugify', 'slugify'),
    ]
    
    print("\n🔧 检查可选依赖:")
    for package_name, import_name in optional_packages:
        check_package(package_name, import_name)
    
    # Django项目特定检查
    print("\n🎯 检查Django项目配置:")
    try:
        import os
        import django
        
        # 设置Django环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbt_blog.settings')
        django.setup()
        
        # 检查应用是否正确注册
        from django.conf import settings
        required_apps = [
            'admin_interface',
            'colorfield', 
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'apps.blog',
            'mdeditor',
        ]
        
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                print(f"✅ 应用 {app} - 已注册")
            else:
                print(f"❌ 应用 {app} - 未注册")
                all_good = False
        
        # 检查模型是否可以导入
        print("\n📊 检查模型导入:")
        try:
            from apps.blog.models import Article, Category, Tag
            print("✅ 博客模型 - 导入成功")
            
            # 检查MDTextField
            from mdeditor.fields import MDTextField
            print("✅ MDTextField - 导入成功")
            
        except ImportError as e:
            print(f"❌ 模型导入失败: {e}")
            all_good = False
        
        # 检查模板标签
        print("\n🏷️ 检查模板标签:")
        try:
            from apps.blog.templatetags.markdown_extras import markdown_format
            print("✅ markdown模板标签 - 导入成功")
        except ImportError as e:
            print(f"❌ 模板标签导入失败: {e}")
            all_good = False
            
    except Exception as e:
        print(f"❌ Django配置检查失败: {e}")
        all_good = False
    
    # 显示已安装的包信息
    print("\n📋 已安装的相关包:")
    installed = get_installed_packages()
    relevant_packages = ['Django', 'django-', 'markdown', 'Pygments', 'asgiref', 'sqlparse']
    
    for line in installed.split('\n'):
        if any(pkg.lower() in line.lower() for pkg in relevant_packages):
            print(f"   {line}")
    
    # 总结
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 所有必需依赖检查通过！项目配置正确。")
        print("\n建议下一步:")
        print("1. 运行 'python manage.py runserver' 启动开发服务器")
        print("2. 访问管理后台测试功能")
        print("3. 测试Markdown编辑器和代码高亮")
    else:
        print("⚠️  发现依赖问题，请检查并安装缺失的包:")
        print("1. pip install -r requirements.txt")
        print("2. 重新运行此检查脚本")
    print("=" * 50)


if __name__ == '__main__':
    main() 