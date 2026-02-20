import json
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from apps.blog.models import OpenSourceProject, ProjectMetricSnapshot


class Command(BaseCommand):
    help = '同步开源项目指标（star/fork/最近提交时间）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-slug',
            dest='project_slug',
            default='',
            help='仅同步指定项目slug',
        )

    def handle(self, *args, **options):
        project_slug = (options.get('project_slug') or '').strip()
        token = (getattr(settings, 'GITHUB_TOKEN', '') or '').strip()
        project_qs = OpenSourceProject.objects.filter(is_active=True)
        if project_slug:
            project_qs = project_qs.filter(slug=project_slug)

        if not project_qs.exists():
            self.stdout.write(self.style.WARNING('没有可同步的开源项目。'))
            return

        if not token:
            for project in project_qs:
                self._upsert_snapshot(
                    project,
                    sync_status=ProjectMetricSnapshot.SYNC_SKIPPED,
                    sync_error='GITHUB_TOKEN 未配置，已跳过同步。',
                    fallback_to_latest=True,
                )
            self.stdout.write(self.style.WARNING('GITHUB_TOKEN 未配置，已跳过同步。'))
            return

        success_count = 0
        failed_count = 0

        for project in project_qs:
            try:
                owner_repo = self._extract_owner_repo(project.github_url)
                metric_data = self._fetch_metric_data(owner_repo, token)
                self._upsert_snapshot(
                    project,
                    stars=metric_data['stars'],
                    forks=metric_data['forks'],
                    last_commit_at=metric_data['last_commit_at'],
                    sync_status=ProjectMetricSnapshot.SYNC_SUCCESS,
                    sync_error='',
                )
                success_count += 1
            except Exception as exc:  # pragma: no cover - 由测试mock覆盖
                self._upsert_snapshot(
                    project,
                    sync_status=ProjectMetricSnapshot.SYNC_FAILED,
                    sync_error=str(exc)[:500],
                    fallback_to_latest=True,
                )
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'open-source metrics sync finished: success={success_count}, failed={failed_count}'
            )
        )

    def _extract_owner_repo(self, github_url):
        parsed = urlparse(github_url)
        if parsed.netloc not in {'github.com', 'www.github.com'}:
            raise ValueError(f'不支持的Github地址：{github_url}')

        path_items = [item for item in parsed.path.strip('/').split('/') if item]
        if len(path_items) < 2:
            raise ValueError(f'仓库地址无效：{github_url}')
        return f'{path_items[0]}/{path_items[1]}'

    def _fetch_metric_data(self, owner_repo, token):
        endpoint = f'https://api.github.com/repos/{owner_repo}'
        request = Request(
            endpoint,
            headers={
                'Accept': 'application/vnd.github+json',
                'Authorization': f'Bearer {token}',
                'User-Agent': 'jbt-blog-open-source-sync/1.0',
            },
        )

        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode('utf-8'))

        pushed_at = payload.get('pushed_at')
        parsed_last_commit = None
        if pushed_at:
            parsed_last_commit = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))

        return {
            'stars': int(payload.get('stargazers_count', 0) or 0),
            'forks': int(payload.get('forks_count', 0) or 0),
            'last_commit_at': parsed_last_commit,
        }

    def _upsert_snapshot(
        self,
        project,
        stars=None,
        forks=None,
        last_commit_at=None,
        sync_status=ProjectMetricSnapshot.SYNC_SKIPPED,
        sync_error='',
        fallback_to_latest=False,
    ):
        metric_date = now().date()
        latest_snapshot = project.latest_snapshot
        snapshot_defaults = {
            'stars': 0,
            'forks': 0,
            'last_commit_at': None,
        }

        if latest_snapshot:
            snapshot_defaults.update(
                {
                    'stars': latest_snapshot.stars,
                    'forks': latest_snapshot.forks,
                    'last_commit_at': latest_snapshot.last_commit_at,
                }
            )

        if not fallback_to_latest:
            if stars is not None:
                snapshot_defaults['stars'] = stars
            if forks is not None:
                snapshot_defaults['forks'] = forks
            if last_commit_at is not None:
                snapshot_defaults['last_commit_at'] = last_commit_at

        snapshot_defaults['sync_status'] = sync_status
        snapshot_defaults['sync_error'] = sync_error

        ProjectMetricSnapshot.objects.update_or_create(
            project=project,
            metric_date=metric_date,
            defaults=snapshot_defaults,
        )
