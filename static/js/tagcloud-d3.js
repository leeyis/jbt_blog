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
            radiusX: options.radiusX || 100,  // 椭球体X轴半径
            radiusY: options.radiusY || 60,   // 椭球体Y轴半径
            radiusZ: options.radiusZ || 80,   // 椭球体Z轴半径
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
        
        // 3D旋转状态
        this.rotation = { x: 0, y: 0 };
        this.isDragging = false;
        this.lastMousePos = { x: 0, y: 0 };
        
        // 自动旋转配置
        this.autoRotate = true;
        this.autoRotateSpeed = 0.002; // 旋转速度
        this.lastInteractionTime = Date.now();
        this.autoRotateDelay = 3000; // 停止交互后3秒开始自动旋转
        
        // 缩放配置
        this.scale = 1.0;
        this.minScale = 0.5;
        this.maxScale = 3.0;
        this.scaleSpeed = 0.1;
        
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
                color: '#47BAC1',  // 使用统一的主题颜色
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
            
        this.nodes = this.processedData.map((d, i) => {
            const text = tempSvg.append('text')
                .style('font-size', d.fontSize + 'px')
                .style('font-family', 'Arial, sans-serif')
                .style('font-weight', '500')
                .text(d.name);
                
            const bbox = text.node().getBBox();
            text.remove();
            
            // 使用球面黄金螺旋分布，然后正确映射到椭球面
            const goldenAngle = Math.PI * (3 - Math.sqrt(5)); // 黄金角度
            const theta = goldenAngle * i; // 方位角
            const v = i / (this.processedData.length - 1); // 标准化参数[0,1]
            const phi = Math.acos(1 - 2 * v); // 极角，均匀分布
            
            // 标准球面坐标
            const sphereX = Math.sin(phi) * Math.cos(theta);
            const sphereY = Math.cos(phi);
            const sphereZ = Math.sin(phi) * Math.sin(theta);
            
            // 映射到椭球面：将球面坐标缩放到椭球
            const ellipsoidX = this.options.radiusX * sphereX;
            const ellipsoidY = this.options.radiusY * sphereY;
            const ellipsoidZ = this.options.radiusZ * sphereZ;
            
            return {
                ...d,
                width: bbox.width + this.options.padding * 2,
                height: bbox.height + this.options.padding * 2,
                // 3D坐标
                x3d: ellipsoidX,
                y3d: ellipsoidY,
                z3d: ellipsoidZ,
                // 投影到2D的坐标（初始化）
                x: this.options.width / 2,
                y: this.options.height / 2,
                // 球面坐标参数
                theta: theta,
                phi: phi,
                // 可见性和深度
                visible: true,
                depth: ellipsoidZ
            };
        });
        
        tempSvg.remove();
        
        // 初始投影
        this.project3DTo2D();
    }
    
    // 3D数学工具方法
    rotateX(point, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        return {
            x: point.x,
            y: point.y * cos - point.z * sin,
            z: point.y * sin + point.z * cos
        };
    }
    
    rotateY(point, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        return {
            x: point.x * cos + point.z * sin,
            y: point.y,
            z: -point.x * sin + point.z * cos
        };
    }
    
    project3DTo2D() {
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        
        this.nodes.forEach(node => {
            // 应用旋转
            let rotated = { x: node.x3d, y: node.y3d, z: node.z3d };
            rotated = this.rotateX(rotated, this.rotation.x);
            rotated = this.rotateY(rotated, this.rotation.y);
            
            // 应用缩放并投影到2D平面
            const scaledX = rotated.x * this.scale;
            const scaledY = rotated.y * this.scale;
            
            node.x = centerX + scaledX;
            node.y = centerY - scaledY; // Y轴反转以匹配屏幕坐标
            node.depth = rotated.z;
            
            // 计算透明度（背面的标签变暗但不隐藏）
            node.visible = true; // 所有标签都保持可见
            // 使用平滑的透明度渐变，背面标签最低透明度为0.6，减小前后差异
            const normalizedZ = (rotated.z + this.options.radiusZ) / (2 * this.options.radiusZ);
            node.opacity = Math.max(0.6, Math.min(1.0, 0.6 + normalizedZ * 0.4));
        });
        
        // 按深度排序（Z坐标），远的在前面绘制
        this.nodes.sort((a, b) => a.depth - b.depth);
    }
    
    setupMouseInteraction() {
        // 添加鼠标拖拽旋转功能
        this.dragStartTime = 0;
        this.dragThreshold = 5; // 像素阈值，区分点击和拖拽
        
        this.svg
            .on('mousedown', (event) => {
                if (event.button === 0) { // 左键
                    this.dragStartTime = Date.now();
                    this.dragStartPos = { x: event.clientX, y: event.clientY };
                    this.lastMousePos = { x: event.clientX, y: event.clientY };
                    this.hasDragged = false;
                }
            })
            .on('mousemove', (event) => {
                if (this.dragStartTime > 0) {
                    const deltaX = event.clientX - this.dragStartPos.x;
                    const deltaY = event.clientY - this.dragStartPos.y;
                    const dragDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                    
                    // 只有当移动距离超过阈值时才开始拖拽
                    if (dragDistance > this.dragThreshold) {
                        this.isDragging = true;
                        this.hasDragged = true;
                        
                        const deltaXMove = event.clientX - this.lastMousePos.x;
                        const deltaYMove = event.clientY - this.lastMousePos.y;
                        
                        // 将鼠标移动转换为旋转（纵向翻转模式）
                        this.rotation.x += deltaXMove * 0.01;  // 水平移动控制纵向翻转
                        this.rotation.y += deltaYMove * 0.01;  // 垂直移动控制水平旋转
                        
                        // 限制X轴旋转范围，防止翻转过度
                        this.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.rotation.x));
                        
                        // 更新投影和显示
                        this.project3DTo2D();
                        this.tick();
                        
                        this.svg.style('cursor', 'grabbing');
                        
                        // 更新最后交互时间，重置自动旋转
                        this.lastInteractionTime = Date.now();
                    }
                    
                    this.lastMousePos = { x: event.clientX, y: event.clientY };
                }
            })
            .on('mouseup', (event) => {
                // 如果没有拖拽，允许点击事件冒泡
                if (!this.hasDragged) {
                    // 不阻止事件，让标签的点击事件正常处理
                } else {
                    // 如果进行了拖拽，更新交互时间并启用自动旋转
                    this.lastInteractionTime = Date.now();
                    this.autoRotate = true;
                }
                
                this.isDragging = false;
                this.dragStartTime = 0;
                this.hasDragged = false;
                this.svg.style('cursor', 'default');
            })
            .on('mouseleave', () => {
                this.isDragging = false;
                this.dragStartTime = 0;
                this.hasDragged = false;
                this.svg.style('cursor', 'default');
            })
            .style('cursor', 'default');
            
        // 添加触摸支持（移动设备）
        this.touchStartDistance = 0;
        this.initialScale = 1.0;
        
        this.svg
            .on('touchstart', (event) => {
                if (event.touches.length === 1) {
                    // 单指拖拽旋转
                    this.isDragging = true;
                    const touch = event.touches[0];
                    this.lastMousePos = { x: touch.clientX, y: touch.clientY };
                    event.preventDefault();
                } else if (event.touches.length === 2) {
                    // 双指缩放
                    this.isDragging = false;
                    const touch1 = event.touches[0];
                    const touch2 = event.touches[1];
                    this.touchStartDistance = Math.sqrt(
                        Math.pow(touch2.clientX - touch1.clientX, 2) +
                        Math.pow(touch2.clientY - touch1.clientY, 2)
                    );
                    this.initialScale = this.scale;
                    event.preventDefault();
                }
            })
            .on('touchmove', (event) => {
                if (event.touches.length === 1 && this.isDragging) {
                    // 单指旋转
                    const touch = event.touches[0];
                    const deltaX = touch.clientX - this.lastMousePos.x;
                    const deltaY = touch.clientY - this.lastMousePos.y;
                    
                    this.rotation.x += deltaX * 0.01;  // 水平移动控制纵向翻转
                    this.rotation.y += deltaY * 0.01;  // 垂直移动控制水平旋转
                    this.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.rotation.x));
                    
                    this.project3DTo2D();
                    this.tick();
                    
                    this.lastMousePos = { x: touch.clientX, y: touch.clientY };
                    this.lastInteractionTime = Date.now();
                    event.preventDefault();
                } else if (event.touches.length === 2) {
                    // 双指缩放
                    const touch1 = event.touches[0];
                    const touch2 = event.touches[1];
                    const currentDistance = Math.sqrt(
                        Math.pow(touch2.clientX - touch1.clientX, 2) +
                        Math.pow(touch2.clientY - touch1.clientY, 2)
                    );
                    
                    if (this.touchStartDistance > 0) {
                        const scaleChange = currentDistance / this.touchStartDistance;
                        const newScale = Math.max(this.minScale, Math.min(this.maxScale, this.initialScale * scaleChange));
                        
                        if (newScale !== this.scale) {
                            this.scale = newScale;
                            this.project3DTo2D();
                            this.tick();
                            this.lastInteractionTime = Date.now();
                        }
                    }
                    event.preventDefault();
                }
            })
            .on('touchend', (event) => {
                if (event.touches.length === 0) {
                    this.isDragging = false;
                    this.touchStartDistance = 0;
                }
            });
            
        // 添加鼠标滚轮缩放
        this.svg.on('wheel', (event) => {
            event.preventDefault();
            
            // 计算缩放变化
            const delta = -event.deltaY * 0.001;
            const newScale = Math.max(this.minScale, Math.min(this.maxScale, this.scale + delta));
            
            if (newScale !== this.scale) {
                this.scale = newScale;
                
                // 更新投影和显示
                this.project3DTo2D();
                this.tick();
                
                // 更新交互时间
                this.lastInteractionTime = Date.now();
            }
        });
    }
    

    
    setupForceSimulation() {
        // 椭球面约束力 - 在3D空间中工作
        const ellipsoidForce = (alpha) => {
            this.nodes.forEach(node => {
                // 计算椭球面方程的值：(x/a)² + (y/b)² + (z/c)² = 1
                const ellipsoidValue = 
                    (node.x3d * node.x3d) / (this.options.radiusX * this.options.radiusX) +
                    (node.y3d * node.y3d) / (this.options.radiusY * this.options.radiusY) +
                    (node.z3d * node.z3d) / (this.options.radiusZ * this.options.radiusZ);
                
                // 如果节点偏离椭球面，施加约束力
                const targetValue = 0.95; // 更接近椭球面
                if (Math.abs(ellipsoidValue - targetValue) > 0.05) {
                    const force = (ellipsoidValue - targetValue) * alpha * 0.05;
                    
                    // 计算椭球面梯度方向
                    const gradX = (2 * node.x3d) / (this.options.radiusX * this.options.radiusX);
                    const gradY = (2 * node.y3d) / (this.options.radiusY * this.options.radiusY);
                    const gradZ = (2 * node.z3d) / (this.options.radiusZ * this.options.radiusZ);
                    
                    // 归一化梯度
                    const gradLength = Math.sqrt(gradX * gradX + gradY * gradY + gradZ * gradZ);
                    if (gradLength > 0) {
                        const scale = force / gradLength;
                        
                        // 在3D空间中调整位置
                        node.x3d -= gradX * scale;
                        node.y3d -= gradY * scale;
                        node.z3d -= gradZ * scale;
                    }
                }
            });
        };
        
        // 3D碰撞检测力
        const collision3D = (alpha) => {
            const nodes = this.nodes;
            for (let i = 0; i < nodes.length; ++i) {
                for (let j = i + 1; j < nodes.length; ++j) {
                    const a = nodes[i];
                    const b = nodes[j];
                    
                    // 3D空间中的距离
                    const dx = b.x3d - a.x3d;
                    const dy = b.y3d - a.y3d;
                    const dz = b.z3d - a.z3d;
                    const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
                    
                    // 计算所需的最小距离（基于2D投影的标签尺寸）
                    const radiusA = Math.sqrt(a.width * a.width + a.height * a.height) / 4;
                    const radiusB = Math.sqrt(b.width * b.width + b.height * b.height) / 4;
                    const minDistance = radiusA + radiusB + 8;
                    
                    if (distance > 0 && distance < minDistance) {
                        const pushForce = (minDistance - distance) * alpha * 0.2;
                        const scale = pushForce / distance;
                        
                        // 在3D空间中推开节点
                        a.x3d -= dx * scale;
                        a.y3d -= dy * scale;
                        a.z3d -= dz * scale;
                        b.x3d += dx * scale;
                        b.y3d += dy * scale;
                        b.z3d += dz * scale;
                    }
                }
            }
        };
        
        // 创建简化的模拟器（不使用D3的force模拟，因为我们在3D空间工作）
        this.simulationActive = true;
        this.simulationAlpha = 1.0;
        
        const simulate = () => {
            if (!this.simulationActive || this.simulationAlpha < 0.01) {
                this.simulationActive = false;
                return;
            }
            
            // 应用力
            ellipsoidForce(this.simulationAlpha);
            collision3D(this.simulationAlpha);
            
            // 重新投影到2D
            this.project3DTo2D();
            
            // 更新显示
            this.tick();
            
            // 降低alpha值，更慢的收敛让分布更稳定
            this.simulationAlpha *= 0.995;
            
            // 继续下一帧
            requestAnimationFrame(simulate);
        };
        
        // 启动模拟
        requestAnimationFrame(simulate);
        
        // 启动自动旋转
        this.startAutoRotation();
    }
    
    startAutoRotation() {
        const autoRotate = () => {
            const now = Date.now();
            const timeSinceInteraction = now - this.lastInteractionTime;
            
            // 如果启用自动旋转且超过延迟时间且没有正在拖拽
            if (this.autoRotate && timeSinceInteraction > this.autoRotateDelay && !this.isDragging && !this.clickedTag) {
                // 缓慢纵向翻转（绕X轴旋转）
                this.rotation.x += this.autoRotateSpeed;
                
                // 重新投影和更新显示
                this.project3DTo2D();
                this.tick();
            }
            
            // 继续下一帧
            requestAnimationFrame(autoRotate);
        };
        
        requestAnimationFrame(autoRotate);
    }
    
    tick() {
        if (this.tagGroups) {
            // 重新排序DOM元素以匹配深度排序
            this.tagGroups
                .sort((a, b) => a.depth - b.depth)
                .attr('transform', d => `translate(${d.x}, ${d.y})`)
                .style('opacity', d => d.opacity);
                
            // 更新文本颜色深度效果
            if (this.textElements) {
                this.textElements
                    .style('fill', d => {
                        const baseColor = d.color;
                        // 根据深度平滑调整颜色亮度，避免突兀变化
                        const normalizedDepth = (d.depth + this.options.radiusZ) / (2 * this.options.radiusZ);
                        const factor = Math.max(0.7, Math.min(1.0, 0.7 + normalizedDepth * 0.3));
                        return this.adjustColorBrightness(baseColor, factor);
                    });
            }
            
            // 保持背景固定透明度，避免拖拽时闪烁
            if (this.backgroundElements) {
                this.backgroundElements
                    .style('fill-opacity', 0.15)
                    .style('stroke-opacity', 0.3);
            }
        }
    }
    
    adjustColorBrightness(hex, factor) {
        // 将十六进制颜色转换为RGB，然后调整亮度
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        
        const newR = Math.round(r * factor);
        const newG = Math.round(g * factor);
        const newB = Math.round(b * factor);
        
        return `rgb(${newR}, ${newG}, ${newB})`;
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
            
        // 在每个组中先创建胶囊形背景
        this.backgroundElements = this.tagGroups
            .append('rect')
            .attr('class', 'tag-background')
            .attr('x', d => -d.width / 2)
            .attr('y', d => -d.height / 2)
            .attr('width', d => d.width)
            .attr('height', d => d.height)
            .attr('rx', d => d.height / 2)  // 设置为高度的一半，创建胶囊形状
            .attr('ry', d => d.height / 2)
            .style('fill', d => d.color)
            .style('opacity', 0.15)
            .style('stroke', d => d.color)
            .style('stroke-width', 1)
            .style('stroke-opacity', 0.3);
            
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
        
        // 在渲染完成后设置鼠标交互功能
        this.setupMouseInteraction();
    }
    
    handleMouseOver(event, d) {
        // 如果正在拖拽，不执行悬停效果
        if (this.isDragging || this.hasDragged) {
            return;
        }
        
        // 暂停3D模拟，防止抖动
        this.simulationActive = false;
        
        // 更新交互时间，暂停自动旋转
        this.lastInteractionTime = Date.now();
        
        // 获取当前标签组
        const tagGroup = d3.select(event.target.parentNode);
        
        // 背景动画效果
        tagGroup.select('.tag-background')
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.2))
            .style('opacity', 0.4)
            .style('stroke-opacity', 0.8)
            .style('stroke-width', 2);
            
        // 文本动画效果
        tagGroup.select('.tag-text')
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.2))
            .style('fill', '#ffffff')
            .style('font-weight', '700')
            .style('filter', 'url(#glow)');
            
        // 整个组的缩放效果
        tagGroup
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.2))
            .attr('transform', `translate(${d.x}, ${d.y}) scale(1.15)`);
            
        // 显示工具提示
        this.showTooltip(event, d);
    }
    
    handleMouseOut(event, d) {
        // 如果正在拖拽，不执行悬停恢复效果
        if (this.isDragging || this.hasDragged) {
            return;
        }
        
        // 获取当前标签组
        const tagGroup = d3.select(event.target.parentNode);
        
        // 背景恢复效果
        tagGroup.select('.tag-background')
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.1))
            .style('opacity', 0.15)
            .style('stroke-opacity', 0.3)
            .style('stroke-width', 1);
            
        // 文本恢复效果
        tagGroup.select('.tag-text')
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.1))
            .style('fill', d.color)
            .style('font-weight', '500')
            .style('filter', 'none');
            
        // 整个组的缩放恢复
        tagGroup
            .transition()
            .duration(200)
            .ease(d3.easeBack.out(1.1))
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
        // 保存原始位置用于恢复
        this.originalClickedPosition = { x: clickedData.x, y: clickedData.y };
        
        // 计算中心位置
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        
        // 暂停3D模拟和自动旋转
        this.simulationActive = false;
        this.autoRotate = false;
        
        // 对所有标签进行动画处理
        this.tagGroups
            .transition()
            .duration(500)
            .ease(d3.easeBackOut.overshoot(1.2))
            .attr('transform', (d) => {
                if (d === clickedData) {
                    // 被点击的标签：视觉上移动到中心并放大，但不修改实际坐标
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
        
        // 重新计算3D投影以获取正确的位置
        this.project3DTo2D();
        
        // 恢复所有标签的状态，使用重新投影后的坐标
        this.tagGroups
            .transition()
            .duration(400)
            .ease(d3.easeQuadOut)
            .attr('transform', (d) => `translate(${d.x}, ${d.y}) scale(1)`)
            .style('opacity', 1);
        
        // 重启3D力模拟
        this.simulationActive = true;
        this.simulationAlpha = 0.3;
        
        // 恢复自动旋转（延迟一段时间后）
        this.lastInteractionTime = Date.now();
        
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
        this.options.radiusX = newWidth * 0.4;
        this.options.radiusY = newHeight * 0.35;
        this.options.radiusZ = Math.min(newWidth, newHeight) * 0.3;
        
        this.svg
            .attr('width', newWidth)
            .attr('height', newHeight);
            
        // 重新计算3D投影
        this.project3DTo2D();
        this.tick();
    }
}

// 初始化函数
function initEllipticalTagCloud() {
    // 移动端检测：如果屏幕宽度小于等于768px，则不初始化3D标签云
    if (window.innerWidth <= 768) {
        console.log('移动端设备，跳过3D标签云初始化');
        return;
    }

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
        radiusX: containerWidth * 0.4,
        radiusY: containerHeight * 0.35,
        radiusZ: Math.min(containerWidth, containerHeight) * 0.3,
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