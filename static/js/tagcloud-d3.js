/**
 * D3.js标签云实现
 * 基于词频动态调整标签大小，支持悬停效果和点击导航
 */

class TagCloud {
    constructor(containerId, options = {}) {
        this.container = d3.select(`#${containerId}`);
        this.width = options.width || 280;
        this.height = options.height || 200;
        this.padding = options.padding || 5;
        this.minFontSize = options.minFontSize || 12;
        this.maxFontSize = options.maxFontSize || 24;
        
        // 创建SVG容器
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('background', 'transparent');
    }
    
    // 计算标签位置，简单的网格布局避免重叠
    calculatePositions(tags) {
        const positions = [];
        const cols = Math.floor(this.width / 60); // 每个标签大约60px宽度
        const rowHeight = 30;
        
        tags.forEach((tag, index) => {
            const row = Math.floor(index / cols);
            const col = index % cols;
            
            positions.push({
                ...tag,
                x: col * (this.width / cols) + Math.random() * 20 - 10, // 添加一些随机偏移
                y: row * rowHeight + 20 + Math.random() * 10 - 5,
                fontSize: this.minFontSize + (tag.size - 1) * (this.maxFontSize - this.minFontSize) / 4
            });
        });
        
        return positions;
    }
    
    // 渲染标签云
    render(data) {
        const tags = this.calculatePositions(data);
        
        // 绑定数据并创建文本元素
        const tagElements = this.svg
            .selectAll('text')
            .data(tags, d => d.text);
        
        // 移除旧元素
        tagElements.exit().remove();
        
        // 添加新元素
        const tagEnter = tagElements
            .enter()
            .append('text')
            .attr('class', 'tag-item')
            .style('cursor', 'pointer')
            .style('font-family', 'Inter, "Microsoft YaHei", sans-serif')
            .style('font-weight', '500')
            .style('fill', '#2c3e50')
            .style('opacity', 0)
            .text(d => d.text)
            .on('mouseover', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style('fill', '#3498db')
                    .style('font-weight', '600')
                    .attr('transform', `translate(${d.x}, ${d.y}) scale(1.1)`);
                    
                // 显示工具提示
                const tooltip = d3.select('body')
                    .append('div')
                    .attr('class', 'tag-tooltip')
                    .style('position', 'absolute')
                    .style('background', 'rgba(0,0,0,0.8)')
                    .style('color', 'white')
                    .style('padding', '8px 12px')
                    .style('border-radius', '4px')
                    .style('font-size', '12px')
                    .style('font-family', 'Inter, "Microsoft YaHei", sans-serif')
                    .style('pointer-events', 'none')
                    .style('z-index', '1000')
                    .style('opacity', 0)
                    .html(`${d.text} (${d.count} 篇文章)`);
                    
                tooltip
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px')
                    .transition()
                    .duration(200)
                    .style('opacity', 1);
            })
            .on('mouseout', function(event, d) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style('fill', '#2c3e50')
                    .style('font-weight', '500')
                    .attr('transform', `translate(${d.x}, ${d.y}) scale(1)`);
                    
                // 移除工具提示
                d3.selectAll('.tag-tooltip').remove();
            })
            .on('click', function(event, d) {
                window.location.href = d.url;
            });
        
        // 更新所有元素（新增和现有）
        tagElements.merge(tagEnter)
            .attr('x', d => d.x)
            .attr('y', d => d.y)
            .style('font-size', d => d.fontSize + 'px')
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .transition()
            .duration(800)
            .style('opacity', 1);
    }
    
    // 从API加载数据并渲染
    loadAndRender() {
        fetch('/api/tagcloud/')
            .then(response => response.json())
            .then(data => {
                this.render(data.tags);
            })
            .catch(error => {
                console.error('标签云数据加载失败:', error);
                // 降级处理：显示错误信息
                this.svg.append('text')
                    .attr('x', this.width / 2)
                    .attr('y', this.height / 2)
                    .attr('text-anchor', 'middle')
                    .style('fill', '#999')
                    .style('font-size', '14px')
                    .text('标签云加载失败');
            });
    }
}

// 页面加载完成后初始化标签云
document.addEventListener('DOMContentLoaded', function() {
    const tagCloudContainer = document.getElementById('d3-tag-cloud');
    if (tagCloudContainer) {
        const tagCloud = new TagCloud('d3-tag-cloud', {
            width: 280,
            height: 200,
            minFontSize: 12,
            maxFontSize: 20
        });
        tagCloud.loadAndRender();
    }
}); 