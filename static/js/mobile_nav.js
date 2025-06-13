document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const collapsibleNav = document.getElementById('collapsible-nav'); // 获取可折叠区域

    if (toggleButton && sidebar) {
        toggleButton.addEventListener('click', function () {
            sidebar.classList.toggle('is-open');

            // 切换按钮图标
            const icon = toggleButton.querySelector('i');
            if (sidebar.classList.contains('is-open')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times'); // 'fa-times'是关闭图标(X)
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    // 新增：自动折叠功能
    if (collapsibleNav && sidebar) {
        collapsibleNav.addEventListener('click', function(event) {
            // 检查侧边栏是否是展开状态，以及点击的是否是一个链接
            const link = event.target.closest('a');
            if (sidebar.classList.contains('is-open') && link) {
                // 是链接，则立即折叠侧边栏
                sidebar.classList.remove('is-open');

                // 并将按钮图标恢复为汉堡菜单
                const icon = toggleButton.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
}); 