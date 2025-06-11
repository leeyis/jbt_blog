function initializeCopyCodeButtons() {
    // 查找所有由Pygments生成的代码块容器
    const highlightBlocks = document.querySelectorAll('.highlight');

    highlightBlocks.forEach(function (block) {
        // 如果按钮已存在，则不重复添加
        if (block.querySelector('.copy-code-button')) {
            return;
        }

        // 创建复制按钮
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.innerHTML = '<i class="fa fa-copy"></i> 复制';
        copyButton.setAttribute('title', '复制代码');

        // 将按钮添加到代码块中
        block.appendChild(copyButton);

        // 为按钮添加点击事件
        copyButton.addEventListener('click', function (e) {
            e.stopPropagation();

            const codeElement = block.querySelector('pre');
            if (!codeElement) {
                console.error("无法在代码块中找到 <pre> 元素。");
                copyButton.innerText = '错误';
                return;
            }

            const codeToCopy = codeElement.textContent || '';

            // 优先使用现代、安全的Clipboard API
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(codeToCopy).then(function () {
                    showSuccess(copyButton);
                }).catch(function (err) {
                    showError(copyButton, err);
                });
            } else {
                // 如果环境不支持，则使用备用方法
                fallbackCopyText(codeToCopy, copyButton);
            }
        });
    });

    function showSuccess(button) {
        button.innerHTML = '<i class="fa fa-check"></i> 已复制!';
        button.classList.add('copied');
        setTimeout(function () {
            button.innerHTML = '<i class="fa fa-copy"></i> 复制';
            button.classList.remove('copied');
        }, 2000);
    }

    function showError(button, err) {
        console.error('无法复制代码: ', err);
        button.innerText = '复制失败';
         setTimeout(function () {
            button.innerHTML = '<i class="fa fa-copy"></i> 复制';
        }, 2000);
    }

    function fallbackCopyText(text, button) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        
        // 避免在屏幕上显示
        textArea.style.position = 'fixed';
        textArea.style.top = 0;
        textArea.style.left = 0;
        textArea.style.width = '2em';
        textArea.style.height = '2em';
        textArea.style.padding = 0;
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';
        textArea.style.background = 'transparent';

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showSuccess(button);
            } else {
                showError(button, 'document.execCommand failed');
            }
        } catch (err) {
            showError(button, err);
        }

        document.body.removeChild(textArea);
    }
}

document.addEventListener('DOMContentLoaded', initializeCopyCodeButtons); 