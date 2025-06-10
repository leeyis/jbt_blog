/**
 * D3.js椭圆形标签云实现
 * 创建椭圆形分布的动态标签云效果
 */

class EllipticalTagCloud {
    constructor(container, data, options = {}) {
        this.container = d3.select(container);
        this.data = data;
        this.options = {
            width: options.width || 300,
            height: options.height || 180,
            ellipseA: options.ellipseA || 120,  // 椭圆长轴
            ellipseB: options.ellipseB || 70,   // 椭圆短轴
            minFontSize: options.minFontSize || 12,
            maxFontSize: options.maxFontSize || 20,
            padding: options.padding || 5,
            colors: options.colors || ['#47BAC1', '#5bc0c7', '#3a9ca3', '#6cc8ce', '#2c8b92'],
            animationDuration: options.animationDuration || 1000,
            ...options
        };
        
        this.svg = null;
        this.nodes = [];
        this.simulation = null;
        
        this.init();
    }
    
    init() {
        // 清除现有内容
        this.container.selectAll('*').remove();
        
        // 创建SVG容器
        this.svg = this.container
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .attr('class', 'd3-tag-cloud-svg');
            
        // 创建可缩放的主组容器
        this.mainGroup = this.svg.append('g')
            .attr('class', 'main-group');
            
        // 创建椭圆背景（可选，用于调试）
        if (this.options.showEllipse) {
            this.mainGroup.append('ellipse')
                .attr('cx', this.options.width / 2)
                .attr('cy', this.options.height / 2)
                .attr('rx', this.options.ellipseA)
                .attr('ry', this.options.ellipseB)
                .attr('fill', 'none')
                .attr('stroke', 'rgba(71, 186, 193, 0.3)')
                .attr('stroke-width', 1)
                .attr('stroke-dasharray', '5,5');
        }
        
        this.processData();
        this.createNodes();
        this.setupForceSimulation();
        this.render();
    }
    
    processData() {
        // 处理数据，计算字体大小
        const maxCount = Math.max(...this.data.map(d => d.count));
        const minCount = Math.min(...this.data.map(d => d.count));
        
        this.processedData = this.data.map((d, i) => {
            const normalizedCount = (d.count - minCount) / (maxCount - minCount) || 0;
            const fontSize = this.options.minFontSize + normalizedCount * (this.options.maxFontSize - this.options.minFontSize);
            
            return {
                ...d,
                fontSize: fontSize,
                color: this.options.colors[i % this.options.colors.length],
                id: `tag-${i}`,
                x: this.options.width / 2,
                y: this.options.height / 2
            };
        });
    }
    
    createNodes() {
        // 创建文本节点并测量尺寸
        const tempSvg = d3.select('body').append('svg')
            .style('position', 'absolute')
            .style('visibility', 'hidden');
            
        this.nodes = this.processedData.map(d => {
            const text = tempSvg.append('text')
                .style('font-size', d.fontSize + 'px')
                .style('font-family', 'Arial, sans-serif')
                .style('font-weight', '500')
                .text(d.name);
                
            const bbox = text.node().getBBox();
            text.remove();
            
            // 生成椭圆上的初始位置
            const angle = Math.random() * 2 * Math.PI;
            const ellipseX = this.options.width / 2 + this.options.ellipseA * Math.cos(angle) * 0.7;
            const ellipseY = this.options.height / 2 + this.options.ellipseB * Math.sin(angle) * 0.7;
            
            return {
                ...d,
                width: bbox.width + this.options.padding * 2,
                height: bbox.height + this.options.padding * 2,
                x: ellipseX,
                y: ellipseY,
                targetX: ellipseX,
                targetY: ellipseY
            };
        });
        
        tempSvg.remove();
    }
    
    setupZoom() {
        // 创建缩放行为
        this.zoom = d3.zoom()
            .scaleExtent([0.5, 3])  // 缩放范围：0.5x到3x
            .on('zoom', (event) => {
                this.mainGroup.attr('transform', event.transform);
            });
            
        // 应用缩放到SVG
        this.svg.call(this.zoom);
        
        // 设置初始缩放以铺满容器
        this.fitToContainer();
    }
    
    fitToContainer() {
        // 等待一小段时间确保标签布局稳定
        setTimeout(() => {
            // 计算实际标签的边界框
            if (!this.textElements || this.textElements.empty()) return;
            
            let minX = Infinity, maxX = -Infinity;
            let minY = Infinity, maxY = -Infinity;
            
            this.textElements.each(function(d) {
                const bbox = this.getBBox();
                minX = Math.min(minX, d.x - bbox.width / 2);
                maxX = Math.max(maxX, d.x + bbox.width / 2);
                minY = Math.min(minY, d.y - bbox.height / 2);
                maxY = Math.max(maxY, d.y + bbox.height / 2);
            });
            
            // 添加内边距
            const padding = 30;
            minX -= padding;
            maxX += padding;
            minY -= padding;
            maxY += padding;
            
            const width = maxX - minX;
            const height = maxY - minY;
            
            // 计算缩放比例以适应容器（稍微保守一点）
            const scale = Math.min(this.options.width / width, this.options.height / height) * 0.9;
            
            // 计算居中偏移
            const translateX = (this.options.width - width * scale) / 2 - minX * scale;
            const translateY = (this.options.height - height * scale) / 2 - minY * scale;
            
            // 应用初始变换
            const transform = d3.zoomIdentity
                .translate(translateX, translateY)
                .scale(scale);
                
            this.svg.transition()
                .duration(800)
                .call(this.zoom.transform, transform);
        }, 500);
    }
    
    setupForceSimulation() {
        // 椭圆约束力
        const ellipseForce = (alpha) => {
            this.nodes.forEach(node => {
                const cx = this.options.width / 2;
                const cy = this.options.height / 2;
                
                const dx = node.x - cx;
                const dy = node.y - cy;
                
                // 椭圆方程：(x/a)² + (y/b)² = 1
                const ellipseRadius = Math.sqrt(
                    (dx * dx) / (this.options.ellipseA * this.options.ellipseA) +
                    (dy * dy) / (this.options.ellipseB * this.options.ellipseB)
                );
                
                // 如果节点超出椭圆边界，施加向内的力
                if (ellipseRadius > 0.8) {
                    const force = (ellipseRadius - 0.8) * alpha * 0.1;
                    const angle = Math.atan2(dy, dx);
                    node.vx -= Math.cos(angle) * force;
                    node.vy -= Math.sin(angle) * force;
                }
            });
        };
        
        // 创建力导向模拟
        this.simulation = d3.forceSimulation(this.nodes)
            .force('collision', d3.forceCollide().radius(d => Math.max(d.width, d.height) / 2 + 2))
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2).strength(0.1))
            .force('ellipse', ellipseForce)
            .alpha(1)
            .alphaDecay(0.02)
            .on('tick', () => this.tick())
            .on('end', () => {
                // 模拟结束后，固定所有节点位置防止抖动
                this.nodes.forEach(node => {
                    node.fx = node.x;
                    node.fy = node.y;
                });
            });
    }
    
    tick() {
        if (this.tagGroups) {
            this.tagGroups
                .attr('transform', d => `translate(${d.x}, ${d.y})`);
        }
    }
    
    render() {
        // 创建标签组容器 - 在可缩放的主组中
        this.tagGroups = this.mainGroup.selectAll('.tag-group')
            .data(this.nodes)
            .enter()
            .append('g')
            .attr('class', 'tag-group')
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .style('cursor', 'pointer')
            .style('opacity', 0)
            .on('mouseover', this.handleMouseOver.bind(this))
            .on('mouseout', this.handleMouseOut.bind(this))
            .on('click', this.handleClick.bind(this));
            
        // 在每个组中创建文本元素
        this.textElements = this.tagGroups
            .append('text')
            .attr('class', 'tag-text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .style('font-size', d => d.fontSize + 'px')
            .style('font-family', 'Arial, sans-serif')
            .style('font-weight', '500')
            .style('fill', d => d.color)
            .text(d => d.name);
            
        // 动画进场效果
        this.tagGroups
            .transition()
            .duration(this.options.animationDuration)
            .delay((d, i) => i * 100)
            .style('opacity', 1);
            
        // 添加悬停时的发光效果 - 增强的滤镜定义（在SVG根节点）
        const defs = this.svg.append('defs');
        const filter = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-100%')
            .attr('y', '-100%')
            .attr('width', '300%')
            .attr('height', '300%');
            
        // 第一层：内发光
        filter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'innerGlow');
            
        // 第二层：外发光
        filter.append('feGaussianBlur')
            .attr('in', 'SourceGraphic')
            .attr('stdDeviation', '6')
            .attr('result', 'outerGlow');
            
        // 颜色矩阵：创建白色发光
        filter.append('feColorMatrix')
            .attr('in', 'outerGlow')
            .attr('values', '0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0')
            .attr('result', 'whiteGlow');
            
        // 合并所有层
        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'whiteGlow');
        feMerge.append('feMergeNode').attr('in', 'innerGlow');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
        
        // 在渲染完成后设置缩放功能
        this.setupZoom();
    }
    
    handleMouseOver(event, d) {
        // 停止任何正在运行的模拟，防止抖动
        if (this.simulation) {
            this.simulation.stop();
        }
        
        const element = d3.select(event.target);
        
        // 优化的悬浮效果 - 明显放大和光晕
        element
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.2))
            .style('fill', '#ffffff')
            .style('font-weight', '700')
            .style('filter', 'url(#glow)')
            .attr('transform', `translate(${d.x}, ${d.y}) scale(1.25)`);
            
        // 显示工具提示
        this.showTooltip(event, d);
    }
    
    handleMouseOut(event, d) {
        const element = d3.select(event.target);
        
        // 优化的退出效果
        element
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.1))
            .style('fill', d.color)
            .style('font-weight', '500')
            .style('filter', 'none')
            .attr('transform', `translate(${d.x}, ${d.y}) scale(1)`);
            
        // 隐藏工具提示
        this.hideTooltip();
    }
    
    handleClick(event, d) {
        console.log('标签被点击:', d.name, '链接:', d.url);
        
        // 阻止默认点击行为
        event.preventDefault();
        event.stopPropagation();
        
        // 添加点击动画效果
        this.animateClickedTag(d);
        
        // 使用AJAX导航，不刷新标签云
        this.navigateToTag(d.url, d.name);
    }
    
    animateClickedTag(clickedData) {
        console.log('开始点击动画，标签:', clickedData.name);
        
        // 保存被点击的标签引用
        this.clickedTag = clickedData;
        
        // 计算椭圆中心位置
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        
        // 停止力模拟以避免干扰动画
        this.simulation.stop();
        
        // 对所有标签进行动画处理
        this.tagGroups
            .transition()
            .duration(500)
            .ease(d3.easeBackOut.overshoot(1.2))
            .attr('transform', (d) => {
                if (d === clickedData) {
                    // 被点击的标签：移动到中心并放大
                    d.x = centerX;
                    d.y = centerY;
                    console.log('移动标签到中心:', centerX, centerY);
                    return `translate(${centerX}, ${centerY}) scale(1.5)`;
                } else {
                    // 其他标签：保持位置但缩小透明度
                    return `translate(${d.x}, ${d.y}) scale(1)`;
                }
            })
            .style('opacity', (d) => d === clickedData ? 1 : 0.3);
            
        // 为被点击的标签添加脉冲光晕效果
        const clickedNode = this.tagGroups
            .filter(d => d === clickedData);
            
        // 添加光晕圆圈
        clickedNode.append('circle')
            .attr('class', 'click-glow')
            .attr('r', 0)
            .attr('fill', 'none')
            .attr('stroke', '#47BAC1')
            .attr('stroke-width', 2)
            .attr('opacity', 0.8)
            .transition()
            .duration(800)
            .ease(d3.easeQuadOut)
            .attr('r', 40)
            .style('opacity', 0)
            .remove();
    }
    
    resetClickState() {
        // 如果没有被点击的标签，直接返回
        if (!this.clickedTag) return;
        
        console.log('重置点击状态');
        
        // 移除光晕效果
        this.tagGroups.selectAll('.click-glow').remove();
        
        // 恢复所有标签的状态
        this.tagGroups
            .transition()
            .duration(400)
            .ease(d3.easeQuadOut)
            .attr('transform', (d) => `translate(${d.x}, ${d.y}) scale(1)`)
            .style('opacity', 1);
            
        // 重启力模拟
        this.simulation.alpha(0.1).restart();
        
        // 清除点击标签引用
        this.clickedTag = null;
    }
    
    navigateToTag(url, tagName) {
        console.log('开始标签导航:', url, tagName);
        
        // 显示加载状态
        this.showLoadingState();
        
        // 使用fetch获取页面内容
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-Tag-Cloud-Request': 'true'
            }
        })
        .then(response => {
            console.log('AJAX响应状态:', response.status);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            console.log('AJAX响应HTML长度:', html.length);
            
            // 解析响应HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // 获取新的内容区域
            const newContent = doc.querySelector('.content');
            const currentContent = document.querySelector('.content');
            
            if (newContent && currentContent) {
                console.log('替换内容区域');
                // 替换内容区域，但保持侧边栏不变
                const newMainContent = newContent.innerHTML;
                currentContent.innerHTML = newMainContent;
                
                // 重新初始化无限滚动（如果存在）
                this.reinitializeInfiniteScroll();
                
                // 更新浏览器URL和标题
                history.pushState({tagName: tagName}, `标签：${tagName}`, url);
                document.title = `${tagName} - 标签文章列表 - jbt Blog`;
                
                // 滚动到顶部
                document.querySelector('.content').scrollTop = 0;
                
                console.log('标签导航完成');
            } else {
                console.error('未找到内容区域');
            }
        })
        .catch(error => {
            console.error('Error loading tag page:', error);
            // 错误时回退到新标签页打开
            window.open(url, '_blank');
        })
        .finally(() => {
            this.hideLoadingState();
            // 恢复标签状态
            setTimeout(() => {
                this.resetClickState();
            }, 300);
        });
    }
    
    showLoadingState() {
        // 在标签云容器上显示加载状态
        const container = document.querySelector('.tag-cloud-container');
        if (container) {
            // 不降低透明度，因为我们有自己的点击动画
            container.style.pointerEvents = 'none';
            
            // 可选：添加一个微妙的加载指示器
            container.style.cursor = 'wait';
        }
    }
    
    hideLoadingState() {
        // 恢复标签云容器状态
        const container = document.querySelector('.tag-cloud-container');
        if (container) {
            container.style.pointerEvents = 'auto';
            container.style.cursor = 'default';
        }
    }
    
    reinitializeInfiniteScroll() {
        // 重新初始化无限滚动功能
        setTimeout(() => {
            // 直接调用无限滚动初始化函数
            if (typeof initInfiniteScroll === 'function') {
                initInfiniteScroll();
            }
        }, 100);
    }
    
    showTooltip(event, d) {
        // 移除任何现有的工具提示
        d3.selectAll('.tag-tooltip').remove();
        
        const tooltip = d3.select('body').append('div')
            .attr('class', 'tag-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.85)')
            .style('color', 'white')
            .style('padding', '6px 10px')
            .style('border-radius', '4px')
            .style('font-size', '11px')
            .style('font-weight', '500')
            .style('pointer-events', 'none')
            .style('z-index', '1000')
            .style('box-shadow', '0 2px 8px rgba(0, 0, 0, 0.3)')
            .style('backdrop-filter', 'blur(4px)')
            .html(`${d.name} <span style="color: #47BAC1;">(${d.count})</span>`);
            
        // 快速显示工具提示
        tooltip.transition()
            .duration(100)
            .style('opacity', 1);
            
        // 更新位置
        const rect = event.target.getBoundingClientRect();
        tooltip
            .style('left', (rect.left + rect.width / 2 - tooltip.node().offsetWidth / 2) + 'px')
            .style('top', (rect.top - 30) + 'px');
    }
    
    hideTooltip() {
        d3.selectAll('.tag-tooltip')
            .transition()
            .duration(100)
            .style('opacity', 0)
            .remove();
    }
    
    // 响应式更新
    resize(newWidth, newHeight) {
        this.options.width = newWidth;
        this.options.height = newHeight;
        this.options.ellipseA = newWidth * 0.4;
        this.options.ellipseB = newHeight * 0.35;
        
        this.svg
            .attr('width', newWidth)
            .attr('height', newHeight);
            
        this.simulation
            .force('center', d3.forceCenter(newWidth / 2, newHeight / 2))
            .alpha(0.3)
            .restart();
    }
}

// 初始化函数
function initEllipticalTagCloud() {
    console.log('开始初始化标签云');
    
    const container = document.querySelector('.tag-cloud-container');
    if (!container) {
        console.error('未找到标签云容器');
        return;
    }
    
    console.log('找到标签云容器:', container);
    
    // 从DOM获取标签数据
    const tagElements = container.querySelectorAll('.tag-data');
    console.log('找到标签数据元素数量:', tagElements.length);
    
    const tagData = Array.from(tagElements).map(el => ({
        name: el.dataset.name,
        count: parseInt(el.dataset.count),
        url: el.dataset.url
    }));
    
    console.log('标签数据:', tagData);
    
    if (tagData.length === 0) {
        console.error('没有标签数据');
        return;
    }
    
    // 响应式宽度
    const containerWidth = container.offsetWidth;
    const containerHeight = Math.min(180, containerWidth * 0.6);
    
    console.log('容器尺寸:', containerWidth, 'x', containerHeight);
    
    const options = {
        width: containerWidth,
        height: containerHeight,
        ellipseA: containerWidth * 0.35,
        ellipseB: containerHeight * 0.35,
        showEllipse: false // 设为true可显示椭圆边界用于调试
    };
    
    // 创建标签云并保存全局引用
    console.log('创建标签云实例');
    window.tagCloudInstance = new EllipticalTagCloud('.tag-cloud-container', tagData, options);
    console.log('标签云创建完成，实例:', window.tagCloudInstance);
}

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM加载完成，开始初始化标签云');
    initEllipticalTagCloud();
});

// 窗口大小改变时重新初始化
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(initEllipticalTagCloud, 300);
});

// 全局标签云实例引用（暂时保留供调试）
// window.tagCloudInstance 已在 initEllipticalTagCloud 中设置

// 处理浏览器返回/前进按钮
window.addEventListener('popstate', (event) => {
    if (event.state) {
        // 重新加载页面以确保状态一致
        window.location.reload();
    }
}); 