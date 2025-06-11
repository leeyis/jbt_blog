document.addEventListener('DOMContentLoaded', function () {
    // 获取按钮元素
    const backToTopButton = document.getElementById('back-to-top');

    if (backToTopButton) {
        // 滚动事件监听
        window.addEventListener('scroll', function () {
            // 当垂直滚动距离大于半个窗口高度时，显示按钮
            if (window.scrollY > window.innerHeight / 2) {
                backToTopButton.classList.add('show');
            } else {
                backToTopButton.classList.remove('show');
            }
        });

        // 点击事件监听
        backToTopButton.addEventListener('click', function (e) {
            e.preventDefault(); // 阻止<a>标签的默认跳转行为
            window.scrollTo({
                top: 0,
                behavior: 'smooth' // 平滑滚动
            });
        });
    }
}); 