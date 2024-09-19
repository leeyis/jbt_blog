# Introduction

一个基于`python3.6`和`Django2.0`的博客。 

A simple blog based on `python3.6` and `Django2.0`.

## requirement
- Django==2.0.3
- django-jet==1.0.7
- django-summernote==0.8.8.6
- pytz==2018.3
  
## Front page

![1](screenshot/f1.png)

---
![2](screenshot/f2.png)


---

## Backend page
![1](screenshot/b1.png)

---

![2](screenshot/b2.png)

---
![3](screenshot/b3.png)

## Quick start
```bash
#创建虚拟环境
conda create -n blog python=3.6 -y
#激活虚拟环境
conda activate blog
#安装依赖包
pip install -r requirements.txt
#启动服务器
python manage.py runserver
```
浏览器访问`http://127.0.0.1:8000`即可访问主页。\
后台页面登录地址为`http://127.0.0.1:8000/admin` \
默认用户名为`jinbitou`，默认密码为`123456` \
注：如果忘记密码或者密码错误，可以执行`python manage.py changepassword jinbitou`修改。
## Features

#### CN
- 文章管理，包括新增、删除和编辑
- 分类管理，包括新增、删除和编辑
- 标签管理，包括新增、删除和编辑
- 列表页展示概要信息、发布时间、分类、浏览次数
- 分页展示
- 点击"阅读全文"显示文章详细内容
- 详情页每刷新一次浏览次数+1
- 文章分类搜索
- 文章标签搜索
- 文章详细页切换上一篇和下一篇文章
- 点击图标回到顶部
- 文章按月归档

#### EN
- Article management, including adding, deleting and editing
- Classified management, including adding, deleting and editing
- Tag management, including adding, deleting and editing
- List page shows summary information, time of release, category, number of visits
- Pagination display
- Click "read the full text" to display the details of the article
- Pages plus one per view
- Search by category
- Search by tag
- switch between previous and next articles
- One-click back to the top
- Monthly archive

## TO-DO

#### CN

- 关键字搜索
- 评论
- 标签云

#### EN

- Keyword search
- Comments
- Tag Cloud