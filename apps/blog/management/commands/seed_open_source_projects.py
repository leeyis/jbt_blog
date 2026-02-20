from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from apps.blog.models import OpenSourceProject, ProjectMetricSnapshot


SEED_PROJECTS = [
    {
        'name': 'jbt_blog',
        'slug': 'jbt-blog',
        'github_url': 'https://github.com/leeyis/jbt_blog',
        'short_description': '现代化 Django 博客系统，支持 Markdown 与可视化管理后台。',
        'tech_stack': 'Django, Python, PostgreSQL, Docker',
        'highlights': '\n'.join(
            [
                'Django 5 架构，博客内容模型清晰且可扩展。',
                '支持 Markdown 编辑与图片粘贴，创作体验友好。',
                '容器化部署链路完整，便于快速上线与迁移。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                '个人技术博客与知识沉淀。',
                '团队内容门户与技术专栏。',
                'Django 内容系统二次开发模板。',
            ]
        ),
        'sort_order': 10,
        'is_featured': True,
        'stars': 146,
        'forks': 51,
        'last_commit_at': '2025-06-16T05:48:34Z',
    },
    {
        'name': 'ip_proxy_pool',
        'slug': 'ip-proxy-pool',
        'github_url': 'https://github.com/leeyis/ip_proxy_pool',
        'short_description': '动态代理池系统，支持抓取、校验与可用性维护。',
        'tech_stack': 'Python, Scrapy, Redis',
        'highlights': '\n'.join(
            [
                '支持动态生成爬虫策略，提升代理抓取效率。',
                '内置代理可用性验证，持续清洗低质量节点。',
                '模块解耦，可按业务场景扩展来源与校验规则。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                '数据采集任务的稳定代理基础设施。',
                '反爬对抗实验与代理质量研究。',
                '多爬虫任务共享代理池的统一管理。',
            ]
        ),
        'sort_order': 20,
        'is_featured': True,
        'stars': 43,
        'forks': 15,
        'last_commit_at': '2018-10-06T13:23:26Z',
    },
    {
        'name': 'moerduo',
        'slug': 'moerduo',
        'github_url': 'https://github.com/leeyis/moerduo',
        'short_description': '跨平台定时音频播放桌面应用，适合听力训练与专注学习。',
        'tech_stack': 'Tauri, TypeScript, Rust',
        'highlights': '\n'.join(
            [
                '基于 Tauri 构建，兼顾性能与跨平台体验。',
                '支持定时播放与自定义音频内容管理。',
                '轻量桌面应用形态，适合长期学习场景。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                '语言学习中的磨耳朵训练。',
                '睡前听读与番茄钟学习配套。',
                '日常通勤音频内容定时播放。',
            ]
        ),
        'sort_order': 30,
        'is_featured': True,
        'stars': 3,
        'forks': 1,
        'last_commit_at': '2025-10-20T09:26:20Z',
    },
    {
        'name': 'antvis-mcp-sse',
        'slug': 'antvis-mcp-sse',
        'github_url': 'https://github.com/leeyis/antvis-mcp-sse',
        'short_description': '基于 AntV 的图表生成 MCP Server，支持 SSE 通信。',
        'tech_stack': 'Node.js, JavaScript, MCP, SSE',
        'highlights': '\n'.join(
            [
                '将图表能力封装为 MCP 服务，便于 AI 工作流调用。',
                '基于 SSE 的实时通信机制，适合流式交互场景。',
                '聚焦生图能力，可快速衔接数据可视化需求。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                'AI Agent 的图表输出能力扩展。',
                '数据看板快速原型与自动化报告。',
                'MCP 生态中的可视化工具链接入。',
            ]
        ),
        'sort_order': 40,
        'is_featured': False,
        'stars': 4,
        'forks': 0,
        'last_commit_at': '2025-06-29T11:43:19Z',
    },
    {
        'name': 'md2html',
        'slug': 'md2html',
        'github_url': 'https://github.com/leeyis/md2html',
        'short_description': 'Markdown 转静态 HTML 的轻量工具，适合快速发布内容。',
        'tech_stack': 'Python, Markdown',
        'highlights': '\n'.join(
            [
                '命令行使用简单，低成本完成文档静态化。',
                '输出结构清晰，便于托管到静态站点。',
                '适合作为文档构建流程中的基础工具。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                '技术文档快速转静态页面。',
                '离线笔记导出与归档。',
                '小型项目说明页自动生成。',
            ]
        ),
        'sort_order': 50,
        'is_featured': False,
        'stars': 2,
        'forks': 0,
        'last_commit_at': '2025-01-16T05:55:39Z',
    },
    {
        'name': 'message_board',
        'slug': 'message-board',
        'github_url': 'https://github.com/leeyis/message_board',
        'short_description': 'Django 留言板练手项目，覆盖基础表单与留言流程。',
        'tech_stack': 'Django, Python',
        'highlights': '\n'.join(
            [
                '聚焦 Django Web 基础能力，结构简单易读。',
                '留言流程完整，适合作为入门实战样例。',
                '可用于快速演示基础 CRUD 与模板渲染。',
            ]
        ),
        'use_cases': '\n'.join(
            [
                'Django 初学者练手项目。',
                '课堂教学与示例演示。',
                '功能迭代前的原型验证。',
            ]
        ),
        'sort_order': 60,
        'is_featured': False,
        'stars': 5,
        'forks': 1,
        'last_commit_at': '2018-03-05T07:25:49Z',
    },
]


def _parse_github_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is not None:
        return parsed
    if value.endswith('Z'):
        return parse_datetime(value.replace('Z', '+00:00'))
    return None


class Command(BaseCommand):
    help = '初始化开源项目墙样例数据（leeyis 代表仓库）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--without-snapshot',
            action='store_true',
            dest='without_snapshot',
            help='只写入项目信息，不初始化指标快照',
        )

    def handle(self, *args, **options):
        metric_date = now().date()
        without_snapshot = options.get('without_snapshot', False)

        created_count = 0
        updated_count = 0
        snapshot_count = 0

        for project_data in SEED_PROJECTS:
            project_defaults = {
                'name': project_data['name'],
                'github_url': project_data['github_url'],
                'short_description': project_data['short_description'],
                'tech_stack': project_data['tech_stack'],
                'highlights': project_data['highlights'],
                'use_cases': project_data['use_cases'],
                'sort_order': project_data['sort_order'],
                'is_featured': project_data['is_featured'],
                'is_active': True,
            }
            project, created = OpenSourceProject.objects.update_or_create(
                slug=project_data['slug'],
                defaults=project_defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            if without_snapshot:
                continue

            ProjectMetricSnapshot.objects.update_or_create(
                project=project,
                metric_date=metric_date,
                defaults={
                    'stars': project_data['stars'],
                    'forks': project_data['forks'],
                    'last_commit_at': _parse_github_datetime(project_data.get('last_commit_at')),
                    'sync_status': ProjectMetricSnapshot.SYNC_SKIPPED,
                    'sync_error': '样例数据初始化（可后续通过同步命令更新）。',
                },
            )
            snapshot_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    'seed open-source projects finished: '
                    f'created={created_count}, updated={updated_count}, snapshots={snapshot_count}'
                )
            )
        )
