document.addEventListener('DOMContentLoaded', function () {
    const contentContainer = document.querySelector('.content');

    // 将需要重新初始化的脚本逻辑封装成一个函数
    function reinitializeScripts() {
        if (typeof initializeCopyCodeButtons === 'function') {
            initializeCopyCodeButtons();
        }
        if (typeof initializeInfiniteScroll === 'function') {
            initializeInfiniteScroll();
        }
    }

    // 初次加载时，确保无限滚动已初始化
    if (typeof initializeInfiniteScroll === 'function') {
        initializeInfiniteScroll();
    }

    function handleNavigation(event) {
        const targetLink = event.target.closest('.category-list a, .archive-list a, .tag-link');
        if (!targetLink) {
            return;
        }
        
        event.preventDefault();
        const url = targetLink.href;

        contentContainer.style.opacity = '0.5';
        contentContainer.style.transition = 'opacity 0.3s ease-out';

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            const newContent = doc.querySelector('.content');
            const newTitle = doc.querySelector('title');

            if (newContent) {
                contentContainer.innerHTML = newContent.innerHTML;
                document.title = newTitle ? newTitle.innerText : '金笔头博客';
                history.pushState({ path: url }, '', url);
                reinitializeScripts();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                // Fallback for unexpected HTML structure
                console.warn('AJAX response did not contain a .content element. Falling back to full load.');
                window.location.href = url;
            }
        })
        .catch(error => {
            console.error('AJAX navigation error:', error);
            window.location.href = url;
        })
        .finally(() => {
            contentContainer.style.opacity = '1';
        });
    }

    document.body.addEventListener('click', handleNavigation);

    window.addEventListener('popstate', function (event) {
        if (event.state && event.state.path) {
            contentContainer.style.opacity = '0.5';
            fetch(event.state.path, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const newContent = doc.querySelector('.content');
                if (newContent) {
                    contentContainer.innerHTML = newContent.innerHTML;
                    reinitializeScripts();
                } else {
                    window.location.reload();
                }
            })
            .catch(error => {
                 console.error('Popstate navigation error:', error);
                 window.location.reload();
            })
            .finally(() => {
                contentContainer.style.opacity = '1';
            });
        }
    });
}); 