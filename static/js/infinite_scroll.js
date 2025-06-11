function initializeInfiniteScroll() {
    const postListContainer = document.querySelector('.blog-post');
    let trigger = document.getElementById('infinite-scroll-trigger');
    let isLoading = false;

    // 清理旧的观察器，以防万一
    if (window.currentInfiniteScrollObserver) {
        window.currentInfiniteScrollObserver.disconnect();
    }
    
    // 如果页面初次加载就没有触发器，说明内容不足一页，直接返回
    if (!postListContainer || !trigger) {
        return;
    }

    const observerCallback = (entries) => {
        // 确保是目标元素进入视野，并且没有在加载中
        if (entries[0].isIntersecting && !isLoading) {
            const nextPage = trigger.getAttribute('data-next-page');

            // 如果没有下一页了，直接断开观察并返回
            if (!nextPage) {
                observer.disconnect();
                return;
            }
            
            isLoading = true;

            let url = new URL(window.location.href);
            url.searchParams.set('page', nextPage);
            
            fetch(url.toString(), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-Infinite-Scroll': 'true'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(html => {
                // 在处理新内容前，先让观察器停止观察旧的触发器
                observer.unobserve(trigger);

                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                const newPosts = tempDiv.querySelectorAll('.post-container');
                const newTrigger = tempDiv.querySelector('#infinite-scroll-trigger');

                // 将新文章插入到旧触发器之前
                newPosts.forEach(post => {
                    postListContainer.insertBefore(post, trigger);
                });

                // 现在可以安全地移除旧触发器了
                trigger.remove();

                if (newTrigger) {
                    // 如果返回内容中有新的触发器
                    postListContainer.appendChild(newTrigger);
                    trigger = newTrigger; // 更新JS变量，指向新的触发器
                    observer.observe(trigger); // **关键步骤：让观察器开始观察新的触发器**
                    isLoading = false; // 重置加载状态
                } else {
                    // 如果没有返回新的触发器，说明是最后一页了
                    observer.disconnect();
                }
            }).catch(error => {
                console.error('Error loading more posts:', error);
                isLoading = false; // 出错时也要重置状态
            });
        }
    };

    const observer = new IntersectionObserver(observerCallback, {
        rootMargin: '0px 0px 400px 0px' // 预加载距离
    });

    // 保存引用并在初次启动时观察第一个触发器
    window.currentInfiniteScrollObserver = observer;
    observer.observe(trigger);
}

// 确保在页面加载和AJAX导航后都能正确初始化
document.addEventListener('DOMContentLoaded', initializeInfiniteScroll);