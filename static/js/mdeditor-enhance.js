// MDEditor 图片粘贴和拖拽上传增强功能
(function() {
    'use strict';

    // 确保脚本只初始化一次
    if (window.mdeditorEnhancerInitialized) {
        return;
    }
    window.mdeditorEnhancerInitialized = true;

    let isUploading = false; // 全局上传状态标志，防止并发上传

    // 等待DOM加载完成
    document.addEventListener('DOMContentLoaded', function() {
        enhanceMDEditor();
    });

    function enhanceMDEditor() {
        const editorContainer = document.querySelector('.editormd, .md-editor, #id_content');
        if (!editorContainer) {
            console.log('MDEditor not found, retrying in 1 second...');
            setTimeout(enhanceMDEditor, 1000);
            return;
        }

        console.log('MDEditor enhancer initialized.');
        editorContainer.classList.add('mdeditor-enhance');
        
        // 唯一的粘贴事件监听器
        document.addEventListener('paste', handlePaste, true); // 使用捕获阶段确保优先处理

        // 拖拽事件监听器
        const dropTarget = editorContainer;
        dropTarget.addEventListener('dragover', handleDragOver);
        dropTarget.addEventListener('drop', handleDrop);
        dropTarget.addEventListener('dragenter', handleDragEnter);
        dropTarget.addEventListener('dragleave', handleDragLeave);
    }
    
    function handlePaste(e) {
        // 检查事件目标是否在我们的编辑器内
        const target = e.target;
        const editorElement = target.closest('.editormd, .md-editor, .CodeMirror') || (target.id === 'id_content' ? target : null);
        
        if (!editorElement) {
            return; // 不是在编辑器内，忽略
        }

        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                console.log('Image paste detected inside editor. Stopping event propagation.');
                // 关键：立即阻止事件的进一步传播和默认行为
                e.preventDefault();
                e.stopPropagation();

                const blob = items[i].getAsFile();
                uploadImage(blob, findTextarea(editorElement));
                return; // 只处理第一张图片
            }
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    }

    function handleDragEnter(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        const targetTextarea = findTextarea(e.currentTarget);

        for (let i = 0; i < files.length; i++) {
            if (files[i].type.indexOf('image') !== -1) {
                uploadImage(files[i], targetTextarea);
                return; // 只处理第一张图片
            }
        }
    }
    
    // 查找编辑器内可用的textarea
    function findTextarea(container) {
        return container.querySelector('textarea, .CodeMirror-code') || container;
    }

    function uploadImage(file, target) {
        if (isUploading) {
            console.warn('Upload already in progress, skipping...');
            alert('已有图片正在上传，请稍候...');
            return;
        }

        isUploading = true;
        console.log('Starting upload for:', file.name);
        showUploadIndicator();

        const formData = new FormData();
        formData.append('editormd-image-file', file, file.name || 'image.png');

        fetch('/mdeditor/uploads/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success === 1) {
                const imageMarkdown = `![${data.alt || 'image'}](${data.url})\n`;
                insertAtCursor(target, imageMarkdown);
                console.log('Upload successful:', data.url);
            } else {
                alert('图片上传失败：' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert('图片上传出错，请检查网络和服务器配置。');
        })
        .finally(() => {
            isUploading = false;
            hideUploadIndicator();
        });
    }

    function insertAtCursor(target, text) {
        const cm = target.closest('.CodeMirror')?.CodeMirror;
        if (cm) {
            cm.replaceSelection(text);
        } else if (target.setRangeText) {
            const start = target.selectionStart;
            const end = target.selectionEnd;
            target.setRangeText(text, start, end, 'end');
        } else {
            target.value += text;
        }
        
        // 触发input事件以更新编辑器状态
        if(target.dispatchEvent) {
            target.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    function showUploadIndicator() {
        let indicator = document.getElementById('upload-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'upload-indicator';
            indicator.className = 'upload-indicator';
            indicator.textContent = '正在上传图片...';
            document.body.appendChild(indicator);
        }
    }

    function hideUploadIndicator() {
        const indicator = document.getElementById('upload-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // 添加基础样式
    const style = document.createElement('style');
    style.textContent = `
        .mdeditor-enhance.drag-over {
            border: 2px dashed #007cba !important;
            background-color: rgba(0, 124, 186, 0.1) !important;
        }
        .upload-indicator {
            position: fixed; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8); color: white;
            padding: 20px; border-radius: 5px;
            z-index: 99999; font-size: 14px;
        }
    `;
    document.head.appendChild(style);

})(); 