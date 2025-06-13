// apps/blog/static/js/article_admin_setup.js

// 使用Django admin推荐的方式来确保jQuery已经加载
if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
    (function($) {
        $(document).ready(function() {
            // 找到标签多选框
            const tagsSelect = $('#id_tags');

            // 如果找不到该元素，则直接退出
            if (tagsSelect.length === 0) {
                return;
            }

            // 隐藏原始的多选框
            tagsSelect.hide();

            // 创建胶囊容器
            const capsuleContainer = $('<div class="tags-capsule-container"></div>');
            tagsSelect.parent().prepend(capsuleContainer);

            // 遍历原始多选框的每个option，创建对应的胶囊
            tagsSelect.find('option').each(function() {
                const option = $(this);
                const value = option.val();
                const text = option.text();
                
                const capsule = $('<span class="tag-capsule"></span>').text(text).attr('data-value', value);

                // 根据原始option的选中状态，初始化胶囊的样式
                if (option.is(':selected')) {
                    capsule.addClass('selected');
                }

                // 添加点击事件
                capsule.on('click', function() {
                    // 切换选中样式
                    $(this).toggleClass('selected');
                    
                    // 同步更新原始option的选中状态
                    const correspondingOption = tagsSelect.find('option[value="' + $(this).data('value') + '"]');
                    if ($(this).hasClass('selected')) {
                        correspondingOption.prop('selected', true);
                    } else {
                        correspondingOption.prop('selected', false);
                    }
                    // 触发change事件，以防有其他JS依赖于它
                    tagsSelect.trigger('change');
                });

                capsuleContainer.append(capsule);
            });

            // --- 新增代码开始 ---
            // 包装Django的dismissAddRelatedObjectPopup函数
            // 以便在通过弹窗添加新标签后，能够动态更新我们的胶囊UI

            // 首先，保存原始函数
            const originalDismissAddRelatedObjectPopup = window.dismissAddRelatedObjectPopup;

            window.dismissAddRelatedObjectPopup = function(win, newId, newRepr) {
                // 调用原始函数，让Django完成它自己的工作
                // (例如，在隐藏的<select>中添加新的<option>)
                originalDismissAddRelatedObjectPopup(win, newId, newRepr);

                // `win.name` 是触发弹窗的<select>元素的id
                // 我们只关心标签字段的弹窗
                if (win.name === 'id_tags') {
                    const newOption = tagsSelect.find('option[value="' + newId + '"]');
                    if (newOption.length > 0) {
                        // 确保新选项被选中
                        newOption.prop('selected', true);

                        // 创建一个新的胶囊
                        const capsule = $('<span class="tag-capsule selected"></span>').text(newRepr).attr('data-value', newId);
                        
                        // 为新胶囊绑定点击事件
                        capsule.on('click', function() {
                            $(this).toggleClass('selected');
                            const correspondingOption = tagsSelect.find('option[value="' + $(this).data('value') + '"]');
                            correspondingOption.prop('selected', $(this).hasClass('selected'));
                            tagsSelect.trigger('change');
                        });
                        
                        // 将新胶囊添加到容器中
                        capsuleContainer.append(capsule);
                    }
                }
            };
            // --- 新增代码结束 ---
        });
    })(django.jQuery);
} 