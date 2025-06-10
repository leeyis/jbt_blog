function initInfiniteScroll() {
    const postListContainer = document.getElementById('post-list-container');
    const trigger = document.getElementById('infinite-scroll-trigger');
    let isLoading = false;

    if (!trigger) {
        return; // 如果没有触发器，说明是最后一页或只有一页
    }
    
    // 如果已经有观察器在运行，先断开
    if (window.currentInfiniteScrollObserver) {
        window.currentInfiniteScrollObserver.disconnect();
    }

    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !isLoading) {
            isLoading = true;
            let nextPage = trigger.getAttribute('data-next-page');

            if (nextPage) {
                // 构建带有查询参数的URL
                let url = window.location.pathname;
                let params = new URLSearchParams(window.location.search);
                params.set('page', nextPage);
                url = `${url}?${params.toString()}`;
                
                fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.text())
                .then(html => {
                    if (html.trim().length > 0) {
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        
                        const newPosts = tempDiv.querySelectorAll('.post-container');
                        newPosts.forEach(post => {
                            postListContainer.appendChild(post);
                        });

                        // 检查并更新下一页的触发器
                        const newTrigger = tempDiv.querySelector('#infinite-scroll-trigger');
                        if (newTrigger) {
                            const newNextPage = newTrigger.getAttribute('data-next-page');
                            trigger.setAttribute('data-next-page', newNextPage);
                            isLoading = false;
                        } else {
                            trigger.remove(); // 没有更多页面了，移除触发器
                            observer.disconnect();
                        }
                    } else {
                        trigger.remove();
                        observer.disconnect();
                    }
                }).catch(error => {
                    console.error('Error loading more posts:', error);
                    isLoading = false; // 出错时重置状态
                });
            }
        }
    }, {
        rootMargin: '0px 0px 200px 0px' // 在距离底部200px时开始加载
    });

    // 保存当前观察器的引用
    window.currentInfiniteScrollObserver = observer;
    observer.observe(trigger);
}

// 初始化
document.addEventListener('DOMContentLoaded', initInfiniteScroll);