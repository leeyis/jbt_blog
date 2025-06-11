#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI/LLM科普文章数据生成脚本
生成20篇Markdown格式的AI和大模型科普文章，包含分类和标签关联
支持一键清空测试数据功能
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
from django.utils import timezone

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbt_blog.settings')
django.setup()

from apps.blog.models import Category, Article, Tag

# AI/LLM分类数据
CATEGORIES = [
    '人工智能基础', '大语言模型', '机器学习', '深度学习', '自然语言处理', 'AI应用', 'AI伦理', 'AI工具'
]

# AI/LLM标签数据
TAGS = [
    'AI', 'LLM', 'GPT', 'Transformer', '机器学习', '深度学习', '神经网络', 'NLP', 
    '自然语言处理', '预训练', '微调', '提示工程', '多模态', '生成式AI', 'ChatGPT', 
    'Claude', '大模型', '人工智能', 'AIGC', '智能助手'
]

# AI/LLM文章数据
ARTICLES = [
    {
        'title': 'ChatGPT现象：大语言模型如何改变世界',
        'category': '大语言模型',
        'tags': ['ChatGPT', 'LLM', '大模型', '生成式AI'],
        'content': '''# ChatGPT现象：大语言模型如何改变世界

## ChatGPT的诞生

2022年11月，OpenAI发布了ChatGPT，这款基于GPT-3.5的对话式AI系统在短短几个月内就获得了全球超过1亿用户，成为历史上增长最快的消费者应用程序。

## 什么是大语言模型？

大语言模型（Large Language Model，LLM）是一种基于深度学习的人工智能系统，通过在海量文本数据上进行训练，学会理解和生成自然语言。

### 核心技术：Transformer架构

ChatGPT基于Transformer架构，这是一种革命性的神经网络设计：

- **自注意力机制**：能够关注输入序列中的重要信息
- **并行处理**：相比传统RNN具有更高的训练效率
- **位置编码**：理解文本中单词的顺序关系
- **多层堆叠**：通过深层网络捕获复杂的语言模式

## 训练过程

大语言模型的训练分为几个阶段：

1. **预训练**：在大规模文本语料上学习语言的基本规律
2. **监督微调**：使用人工标注的对话数据进行优化
3. **强化学习**：通过人类反馈进一步改善模型表现

### 数据规模的重要性

ChatGPT的训练数据包含：
- 互联网文本：网页、文章、论坛讨论
- 书籍和文献：经典著作、学术论文
- 代码库：编程语言和算法实现
- 百科知识：结构化的知识内容

## 能力与应用

ChatGPT展现出令人惊叹的能力：

- **文本生成**：创作文章、故事、诗歌
- **问答系统**：回答各领域专业问题
- **代码编写**：编程助手和代码调试
- **语言翻译**：多语言之间的准确翻译
- **内容总结**：提取文档要点

## 局限性与挑战

尽管强大，ChatGPT仍有局限：

- **知识截止时间**：无法获取最新信息
- **事实准确性**：可能产生错误或虚构内容
- **逻辑推理**：在复杂推理任务中可能出错
- **偏见问题**：训练数据中的偏见可能被放大

## 对社会的影响

ChatGPT的出现带来深远影响：

- **教育变革**：改变学习和教学方式
- **工作模式**：自动化部分知识工作
- **内容创作**：降低创作门槛
- **人机交互**：更自然的人机对话界面

大语言模型代表了人工智能发展的重要里程碑，预示着AI技术将更深入地融入人类社会的各个方面。'''
    },
    {
        'title': 'Transformer架构：现代AI的核心引擎',
        'category': '深度学习',
        'tags': ['Transformer', '神经网络', 'AI', '深度学习'],
        'content': '''# Transformer架构：现代AI的核心引擎

## 革命性的突破

2017年，Google团队发表了著名论文"Attention is All You Need"，提出了Transformer架构。这一创新彻底改变了自然语言处理领域，成为现代大语言模型的基础。

## 传统方法的局限

在Transformer出现之前，自然语言处理主要依赖：

- **循环神经网络（RNN）**：顺序处理，训练速度慢
- **卷积神经网络（CNN）**：难以捕获长距离依赖
- **长短期记忆网络（LSTM）**：仍然存在梯度消失问题

### 并行处理的需求

传统序列模型的串行特性限制了：
- 训练效率：无法充分利用GPU并行计算
- 长序列处理：长距离依赖关系难以学习
- 计算复杂度：时间复杂度随序列长度线性增长

## Transformer的核心创新

### 自注意力机制（Self-Attention）

自注意力机制允许模型：
- 直接计算序列中任意两个位置的关系
- 并行处理所有位置的信息
- 捕获长距离依赖关系

计算过程：
1. **查询（Query）**：当前位置的信息查询
2. **键（Key）**：所有位置的信息索引
3. **值（Value）**：实际的信息内容

### 多头注意力（Multi-Head Attention）

通过多个注意力头：
- 学习不同类型的关系模式
- 提高模型的表达能力
- 增强特征提取的多样性

### 位置编码（Positional Encoding）

由于没有递归结构，Transformer需要：
- 显式地编码位置信息
- 使用三角函数生成位置向量
- 保持位置的相对关系

## 编码器-解码器结构

### 编码器（Encoder）
- 6层相同的层堆叠
- 每层包含多头自注意力和前馈网络
- 残差连接和层归一化

### 解码器（Decoder）
- 6层解码器层
- 包含掩码自注意力机制
- 编码器-解码器注意力

## 训练技巧

### 残差连接
- 解决深层网络的梯度消失问题
- 允许信息直接传递到后续层
- 提高训练稳定性

### 层归一化
- 加速训练收敛
- 提高模型稳定性
- 减少内部协变量偏移

### 学习率调度
- Warm-up策略：初期小学习率
- 余弦退火：逐渐减小学习率
- 梯度裁剪：防止梯度爆炸

## 广泛应用

Transformer架构催生了众多成功模型：

- **BERT**：双向编码器表示
- **GPT系列**：生成式预训练Transformer
- **T5**：文本到文本传输Transformer
- **Vision Transformer**：将Transformer应用于图像
- **多模态模型**：结合文本、图像、音频

## 未来发展

Transformer的发展方向：
- **效率优化**：减少计算复杂度
- **长序列处理**：处理更长的输入
- **架构创新**：新的注意力机制
- **跨模态融合**：统一多种数据类型

Transformer不仅改变了NLP，更成为了通用的序列建模架构，为人工智能的发展开辟了新的道路。'''
    }
]

def create_categories():
    """创建科普分类"""
    print("正在创建分类...")
    created_categories = {}
    
    for cat_name in CATEGORIES:
        category, created = Category.objects.get_or_create(name=cat_name)
        created_categories[cat_name] = category
        if created:
            print(f"✅ 创建分类: {cat_name}")
        else:
            print(f"📝 分类已存在: {cat_name}")
    
    return created_categories

def create_tags():
    """创建标签"""
    print("\n正在创建标签...")
    created_tags = {}
    
    for tag_name in TAGS:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        created_tags[tag_name] = tag
        if created:
            print(f"✅ 创建标签: {tag_name}")
        else:
            print(f"📝 标签已存在: {tag_name}")
    
    return created_tags

def generate_more_articles():
    """生成更多AI/LLM文章数据"""
    titles_and_categories = [
        ('机器学习入门：从零开始理解AI', '机器学习', ['机器学习', 'AI', '入门']),
        ('神经网络的工作原理详解', '深度学习', ['神经网络', '深度学习', 'AI']),
        ('自然语言处理技术发展史', '自然语言处理', ['NLP', '自然语言处理', 'AI']),
        ('GPT系列模型演进之路', '大语言模型', ['GPT', 'LLM', '大模型']),
        ('BERT模型：双向编码器的突破', '自然语言处理', ['BERT', 'NLP', '预训练']),
        ('提示工程：与AI对话的艺术', 'AI应用', ['提示工程', 'Prompt', 'AI']),
        ('AI绘画工具：创意与技术的融合', 'AI应用', ['AI绘画', 'AIGC', '创意']),
        ('强化学习：让AI学会决策', '机器学习', ['强化学习', 'AI', '决策']),
        ('计算机视觉：让机器看懂世界', 'AI应用', ['计算机视觉', 'CV', 'AI']),
        ('多模态AI：融合视觉与语言', '深度学习', ['多模态', 'AI', '融合']),
        ('AI代码助手：程序员的新伙伴', 'AI工具', ['代码助手', 'Copilot', 'AI']),
        ('大模型的安全性与对齐问题', 'AI伦理', ['AI安全', '对齐', '伦理']),
        ('联邦学习：保护隐私的AI训练', '机器学习', ['联邦学习', '隐私', 'AI']),
        ('边缘AI：将智能带到设备端', 'AI应用', ['边缘AI', '设备端', 'AI']),
        ('AI在医疗领域的应用前景', 'AI应用', ['医疗AI', '健康', 'AI']),
        ('量化交易中的机器学习应用', 'AI应用', ['量化交易', '金融AI', 'AI']),
        ('AI偏见问题及其解决方案', 'AI伦理', ['AI偏见', '公平性', '伦理']),
        ('AutoML：自动化机器学习的未来', '机器学习', ['AutoML', '自动化', 'AI'])
    ]
    
    return titles_and_categories

def create_article_content(title, category_name):
    """根据标题和分类生成文章内容"""
    content_templates = {
        '机器学习入门：从零开始理解AI': '''# 机器学习入门：从零开始理解AI

## 什么是机器学习？

机器学习（Machine Learning，ML）是人工智能的一个重要分支，它使计算机系统能够自动学习并改进，而无需明确编程。通过分析大量数据，机器学习算法可以识别模式、做出预测和决策。

## 机器学习的类型

### 监督学习
- **定义**：使用标记数据进行训练
- **应用**：分类、回归问题
- **例子**：邮件垃圾过滤、房价预测

### 无监督学习
- **定义**：从无标记数据中发现隐藏模式
- **应用**：聚类、降维、异常检测
- **例子**：客户分群、数据压缩

### 强化学习
- **定义**：通过与环境交互学习最优策略
- **应用**：游戏AI、自动驾驶
- **例子**：AlphaGo、自动交易系统

## 核心概念

### 特征工程
特征是模型输入的数据属性：
- 特征选择：选择最相关的特征
- 特征变换：标准化、归一化
- 特征创建：组合现有特征创造新特征

### 模型训练与评估
1. **数据分割**：训练集、验证集、测试集
2. **模型训练**：算法学习数据模式
3. **性能评估**：准确率、召回率、F1分数
4. **模型优化**：调参、交叉验证

## 常见算法

### 线性回归
- 简单易懂的基础算法
- 适用于连续值预测
- 可解释性强

### 决策树
- 类似人类决策过程
- 易于理解和解释
- 可处理分类和回归问题

### 随机森林
- 多个决策树的集成
- 提高预测准确性
- 减少过拟合风险

### 支持向量机（SVM）
- 寻找最优分类边界
- 适用于高维数据
- 内核技巧处理非线性问题

## 实际应用

机器学习已渗透到生活的各个方面：

- **推荐系统**：Netflix、Amazon的个性化推荐
- **图像识别**：人脸识别、医学影像诊断
- **自然语言处理**：机器翻译、智能客服
- **金融服务**：信用评分、风险控制
- **交通出行**：导航优化、自动驾驶

## 学习路径建议

1. **数学基础**：线性代数、概率统计、微积分
2. **编程技能**：Python/R、数据处理库
3. **理论学习**：算法原理、模型评估
4. **实践项目**：Kaggle竞赛、开源项目
5. **持续学习**：跟踪最新研究、社区交流

机器学习是一个快速发展的领域，掌握其基本概念和方法将为进入AI时代奠定坚实基础。''',
        
        '神经网络的工作原理详解': '''# 神经网络的工作原理详解

## 生物神经元的启发

神经网络的设计灵感来源于人脑的神经元结构。生物神经元通过树突接收信号，在细胞体中处理信息，最后通过轴突传递输出信号。

## 人工神经元模型

### 感知器
最简单的人工神经元包含：
- **输入**：x₁, x₂, ..., xₙ
- **权重**：w₁, w₂, ..., wₙ  
- **偏置**：b
- **激活函数**：f(z)
- **输出**：y = f(Σwᵢxᵢ + b)

### 激活函数的作用
激活函数引入非线性：
- **Sigmoid**：输出范围(0,1)，适合概率输出
- **ReLU**：解决梯度消失，计算高效
- **Tanh**：输出范围(-1,1)，零中心化
- **Softmax**：多分类问题的概率分布

## 多层神经网络

### 网络结构
- **输入层**：接收原始数据
- **隐藏层**：提取特征和模式
- **输出层**：产生最终预测

### 前向传播
信息从输入层逐层传递到输出层：
1. 加权求和：z = Wx + b
2. 激活函数：a = f(z)
3. 层层传递直到输出

### 反向传播
通过梯度下降优化权重：
1. **损失计算**：比较预测与真实值
2. **梯度计算**：链式法则求导
3. **权重更新**：w = w - α∇w
4. **重复迭代**：直到收敛

## 深度学习

### 深层网络的优势
- **分层特征学习**：低层学习基础特征，高层学习抽象概念
- **表示学习**：自动发现数据的有效表示
- **端到端学习**：从原始输入直接到最终输出

### 常见架构
- **卷积神经网络（CNN）**：擅长图像处理
- **循环神经网络（RNN）**：处理序列数据
- **Transformer**：注意力机制，处理长序列
- **生成对抗网络（GAN）**：生成新数据

## 训练技巧

### 正则化
防止过拟合：
- **Dropout**：随机丢弃神经元
- **L1/L2正则化**：权重惩罚
- **批量归一化**：稳定训练过程

### 优化算法
- **SGD**：随机梯度下降
- **Adam**：自适应学习率
- **RMSprop**：解决学习率衰减问题

### 学习率调度
- **固定学习率**：简单但可能不优
- **学习率衰减**：训练过程中逐渐减小
- **周期性调整**：循环变化提高性能

## 实际应用

神经网络在各领域大放异彩：

- **计算机视觉**：图像分类、目标检测、人脸识别
- **自然语言处理**：机器翻译、文本生成、情感分析
- **语音识别**：语音转文字、语音合成
- **推荐系统**：个性化推荐、广告投放
- **医疗诊断**：医学影像分析、药物发现

## 挑战与发展

### 当前挑战
- **可解释性**：黑盒模型难以解释
- **数据需求**：需要大量标注数据
- **计算资源**：训练成本高昂
- **泛化能力**：在新数据上的表现

### 未来发展
- **神经架构搜索**：自动设计网络结构
- **小样本学习**：减少数据依赖
- **联邦学习**：保护隐私的分布式训练
- **神经符号融合**：结合符号推理与神经网络

神经网络作为深度学习的核心，正在重塑人工智能的发展轨迹，为创造更智能的系统提供强大工具。'''
    }
    
    # 如果有预定义的内容就使用，否则生成通用内容
    if title in content_templates:
        return content_templates[title]
    else:
        return f'''# {title}

## 引言

{title}是{category_name}领域中一个重要的研究方向，对于我们理解人工智能技术具有重要意义。

## 基本概念

在{category_name}研究中，{title.replace('的', '').replace('与', '').replace('：', '').split('及')[0]}扮演着关键角色。通过深入研究，研究者们发现了许多有趣的现象和规律。

### 技术发展历程

这一领域的研究起源于计算机科学的早期发展，随着算力提升和数据爆炸，相关技术得到了快速发展。

## 核心特点

研究表明，这一技术具有以下重要特征：

- 具有强大的数据处理能力
- 能够从数据中自动学习模式
- 在实际应用中表现出色
- 对AI发展产生深远影响

## 技术原理

研究者们采用多种方法来实现这一技术：

1. **数据处理**：通过大规模数据训练
2. **算法优化**：不断改进算法性能
3. **模型评估**：建立科学的评估体系
4. **工程实践**：将理论转化为实际应用

## 实际应用

这一技术在多个领域都有重要应用：

- **智能助手**：提升人机交互体验
- **自动化系统**：提高工作效率
- **数据分析**：发现数据中的洞察
- **创新应用**：催生新的商业模式

## 发展趋势

### 技术挑战
- 计算资源需求巨大
- 数据质量要求高
- 模型可解释性有待提升
- 安全性和隐私保护

### 未来方向
- 算法效率持续优化
- 应用场景不断扩展
- 跨领域融合加深
- 产业化程度提高

随着人工智能技术的不断发展，这一领域的研究前景十分广阔。我们相信，未来会有更多令人惊喜的突破，为人类社会的智能化发展做出更大贡献。

通过持续的技术创新和应用探索，我们将能够更好地利用AI技术的潜力，为构建更智能的未来奠定基础。'''

def create_articles(categories, tags):
    """创建文章"""
    print("\n正在创建文章...")
    
    # 合并预定义文章和生成的文章
    all_article_data = ARTICLES.copy()
    additional_titles = generate_more_articles()
    
    # 为额外的文章生成内容
    for title, cat_name, tag_names in additional_titles:
        article_data = {
            'title': title,
            'category': cat_name,
            'tags': tag_names,
            'content': create_article_content(title, cat_name)
        }
        all_article_data.append(article_data)
    
    created_articles = []
    base_time = timezone.now() - timedelta(days=30)
    
    for i, article_data in enumerate(all_article_data):
        # 检查文章是否已存在
        if Article.objects.filter(title=article_data['title']).exists():
            print(f"📝 文章已存在: {article_data['title']}")
            continue
        
        # 创建文章
        pub_time = base_time + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        article = Article.objects.create(
            title=article_data['title'],
            content=article_data['content'],
            status='p',
            category=categories[article_data['category']],
            pub_time=pub_time,
            views=random.randint(10, 500)
        )
        
        # 添加标签
        for tag_name in article_data['tags']:
            if tag_name in tags:
                article.tags.add(tags[tag_name])
        
        created_articles.append(article)
        print(f"✅ 创建文章: {article.title}")
    
    return created_articles

def clear_test_data():
    """清空所有测试数据"""
    print("⚠️  即将清空所有测试数据！")
    confirm = input("请输入 'YES' 确认删除所有文章、分类和标签: ")
    
    if confirm == 'YES':
        # 删除文章（会自动清除文章-标签关联）
        article_count = Article.objects.count()
        Article.objects.all().delete()
        print(f"✅ 已删除 {article_count} 篇文章")
        
        # 删除分类
        category_count = Category.objects.count()
        Category.objects.all().delete()
        print(f"✅ 已删除 {category_count} 个分类")
        
        # 删除标签
        tag_count = Tag.objects.count()
        Tag.objects.all().delete()
        print(f"✅ 已删除 {tag_count} 个标签")
        
        print("\n🎉 所有测试数据已清空！")
    else:
        print("❌ 取消删除操作")

def show_current_data():
    """显示当前数据统计"""
    print("=== 当前数据统计 ===")
    print(f"📄 文章总数: {Article.objects.count()}")
    print(f"   - 已发布: {Article.objects.filter(status='p').count()}")
    print(f"   - 草稿: {Article.objects.filter(status='d').count()}")
    print(f"📁 分类总数: {Category.objects.count()}")
    print(f"🏷️  标签总数: {Tag.objects.count()}")
    
    print("\n--- 分类详情 ---")
    for category in Category.objects.all():
        article_count = Article.objects.filter(category=category).count()
        print(f"  {category.name}: {article_count} 篇文章")

def main():
    print("=== AI/LLM科普文章数据生成脚本 ===")
    print("1. 生成测试数据")
    print("2. 清空测试数据") 
    print("3. 查看当前数据")
    print("4. 退出")
    
    while True:
        choice = input("\n请选择操作 (1-4): ").strip()
        
        if choice == '1':
            print("\n正在生成AI/LLM科普文章...")
            # 创建分类和标签
            categories = create_categories()
            tags = create_tags()
            # 创建文章
            articles = create_articles(categories, tags)
            print(f"\n=== 生成完成 ===")
            print(f"共创建 {len(articles)} 篇新文章")
            show_current_data()
            
        elif choice == '2':
            clear_test_data()
            
        elif choice == '3':
            show_current_data()
            
        elif choice == '4':
            print("👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请输入 1-4")

if __name__ == "__main__":
    main() 