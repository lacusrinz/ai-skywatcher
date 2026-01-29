/**
 * 3D Celestial Sphere (天球) Canvas - 中心视角版本
 * 观测者位于天球中心，向外观看上半球
 */
export class SkyMapCanvas {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // 从 options 获取宽高，或使用默认值
    const width = options.width || 800;
    const height = options.height || 800;

    this.config = {
      width: width,
      height: height,
      centerX: options.centerX || width / 2,           // 动态计算中心 X
      centerY: options.centerY || height * 0.9,        // 动态计算中心 Y（下移 90%）
      radius: options.radius || Math.max(width, height) * 0.75,  // 动态计算半径（最大边的 90%）
      fov: options.fov || 90                           // 视场角（扩大以获得更广阔视野）
    };

    // 观测者视角（位于天球中心，只能转头）
    this.view = {
      azimuth: 0,        // 观测方位角 (0-360°, 0=北)
      altitude: 0,       // 观测高度角 (0-90°, 0=地平线, 90=天顶) - 平视地平线
      zoom: 1.0
    };

    this.state = {
      time: new Date(),
      targets: [],
      zones: [],
      hoveredTarget: null,
      isDragging: false,
      lastMouseX: 0,
      lastMouseY: 0,
      // FOV 框状态
      fovFrame: {
        center: { azimuth: 180, altitude: 45 },
        isVisible: true,
        isSelected: false,
        isDragging: false
      },
      // 月球状态
      moon: {
        position: null,  // { azimuth, altitude, distance, ra, dec }
        phase: null,     // { name, percentage, age_days }
        visible: false,
        hovered: false,
        selected: false,
        showHeatmap: false,
        heatmapData: null  // { grid: [[{alt, az, pollution}]], resolution }
      }
    };

    this.init();
  }

  init() {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.config.width * dpr;
    this.canvas.height = this.config.height * dpr;
    this.canvas.style.width = `${this.config.width}px`;
    this.canvas.style.height = `${this.config.height}px`;
    this.ctx.scale(dpr, dpr);

    this.bindEvents();
    this.render();
  }

  bindEvents() {
    // 鼠标拖动控制视角（原地转头）
    this.canvas.addEventListener('mousedown', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // 优先检测是否点击在 FOV 框上
      if (this.isPointInFOVFrame(x, y)) {
        this.state.fovFrame.isDragging = true;
        this.state.fovFrame.isSelected = true;
        this.state.isDragging = true;
        this.state.lastMouseX = e.clientX;
        this.state.lastMouseY = e.clientY;
        this.canvas.style.cursor = 'grabbing';
        this.render();
        return;
      }

      // 原有的视角拖动逻辑
      this.state.isDragging = true;
      this.state.lastMouseX = e.clientX;
      this.state.lastMouseY = e.clientY;
      this.canvas.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
      // FOV 框拖动优先
      if (this.state.fovFrame.isDragging) {
        const deltaX = e.clientX - this.state.lastMouseX;
        const deltaY = e.clientY - this.state.lastMouseY;

        // 灵敏度：1 像素 ≈ 0.1 度
        const sensitivity = 0.1;
        this.state.fovFrame.center.azimuth =
          (this.state.fovFrame.center.azimuth - deltaX * sensitivity + 360) % 360;
        this.state.fovFrame.center.altitude = Math.max(0, Math.min(90,
          this.state.fovFrame.center.altitude + deltaY * sensitivity
        ));

        this.state.lastMouseX = e.clientX;
        this.state.lastMouseY = e.clientY;

        this.render();
        this.onFOVFrameMove?.(this.state.fovFrame.center);
        return;
      }

      // 原有的视角拖动逻辑
      if (this.state.isDragging) {
        const deltaX = e.clientX - this.state.lastMouseX;
        const deltaY = e.clientY - this.state.lastMouseY;

        // 更新视角（原地转头）
        this.view.azimuth = (this.view.azimuth + deltaX * 0.5 + 360) % 360;
        this.view.altitude = Math.max(0, Math.min(90, this.view.altitude - deltaY * 0.3));

        this.state.lastMouseX = e.clientX;
        this.state.lastMouseY = e.clientY;

        this.render();
      }
    });

    document.addEventListener('mouseup', () => {
      if (this.state.fovFrame.isDragging) {
        this.state.fovFrame.isDragging = false;
        this.canvas.style.cursor = 'grab';
        this.onFOVFrameChange?.(this.state.fovFrame.center);
      }
      this.state.isDragging = false;
      this.canvas.style.cursor = 'grab';
    });

    // 悬停检测
    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.state.isDragging && !this.state.fovFrame.isDragging) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // 检测 FOV 框悬停
        if (this.isPointInFOVFrame(x, y)) {
          this.canvas.style.cursor = 'grab';
          // 高亮效果
          if (!this.state.fovFrame.isSelected) {
            this.state.fovFrame.isSelected = true;
            this.render();
          }
        } else {
          if (this.state.fovFrame.isSelected) {
            this.state.fovFrame.isSelected = false;
            this.render();
          }
          this.handleHover(x, y);
        }
      }
    });

    // 点击选择
    this.canvas.addEventListener('click', (e) => {
      if (this.state.hoveredTarget && !this.state.isDragging && !this.state.fovFrame.isDragging) {
        this.onTargetSelect?.(this.state.hoveredTarget);
      }
    });

    // 滚轮缩放
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY > 0 ? 0.95 : 1.05;
      this.view.zoom = Math.max(0.5, Math.min(3.0, this.view.zoom * zoomFactor));
      this.render();
    });

    this.canvas.style.cursor = 'grab';
  }

  /**
   * 从天球中心向外看的3D投影
   * 观测者位于 (0, 0, 0)，向外看天球内表面
   * @param {number} azimuth - 方位角（度）
   * @param {number} altitude - 高度角（度）
   * @returns {Object} { x, y, z, visible, scale }
   */
  projectFromCenter(azimuth, altitude) {
    // 转换为弧度
    const az = azimuth * (Math.PI / 180);
    const alt = altitude * (Math.PI / 180);

    // 观测者的视角旋转
    const viewAz = this.view.azimuth * (Math.PI / 180);
    const viewAlt = this.view.altitude * (Math.PI / 180);

    // 先应用观测者的方位角旋转（绕Y轴）
    const x1 = Math.sin(az - viewAz) * Math.cos(alt);
    const y1 = Math.sin(alt);
    const z1 = Math.cos(az - viewAz) * Math.cos(alt);

    // 再应用观测者的高度角倾斜（绕X轴）
    const y2 = y1 * Math.cos(viewAlt) - z1 * Math.sin(viewAlt);
    const z2 = y1 * Math.sin(viewAlt) + z1 * Math.cos(viewAlt);
    const x2 = x1;

    // 目标在天球内表面
    const R = this.config.radius;
    const x = x2 * R;
    const y = y2 * R;
    const z = z2 * R;

    // 从原点向外看的透视投影
    // 观测者在原点，目标在 (x, y, z)
    // 透视投影：screenX = x / z, screenY = y / z

    // 只显示前半球（z > 0），包括地平线（y >= 0）
    // 注意：这里使用的是已经应用视角旋转后的 y 坐标
    const visible = z > 0 && y >= -50; // 允许略微向下看，显示更多区域

    // 透视投影（使用极弱透视接近正交投影）
    // perspective 很大时，scale ≈ 1，接近原始大小
    const perspective = 10000; // 极大的透视距离，让地平线接近原始尺寸
    const scale = perspective / (z + perspective) * this.view.zoom;

    // 水平方向额外放大，让天球填满画布宽度
    // 画布宽度 800， centerX 400，期望地平线圆半径接近 400
    const horizontalScale = 1; // 水平方向放大 2 倍

    const screenX = this.config.centerX + x * scale * horizontalScale;
    const screenY = this.config.centerY - y * scale; // Y轴向上为正

    return {
      x: screenX,
      y: screenY,
      z: z,
      visible: visible,
      scale: scale
    };
  }

  render() {
    const { ctx, config } = this;

    ctx.clearRect(0, 0, config.width, config.height);

    this.drawBackground();
    this.drawCelestialSphere();
    this.drawGrid();
    this.drawHorizon();
    this.drawVisibleZones();  // 绘制可视区域
    this.drawFOVFrame();      // 绘制 FOV 框
    this.drawMoon();
    this.drawTargets();
    this.drawCompass();
  }

  drawBackground() {
    const { ctx, config } = this;

    // 深空渐变背景（从中心向外）
    const gradient = ctx.createRadialGradient(
      config.centerX, config.centerY, 0,
      config.centerX, config.centerY, config.radius * 1.2
    );
    gradient.addColorStop(0, '#0A0A14');      // 天顶（深色）
    gradient.addColorStop(0.5, '#12121F');   // 中间
    gradient.addColorStop(1, '#1A1A2E');     // 地平线（稍亮）

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, config.width, config.height);
  }

  drawCelestialSphere() {
    const { ctx, config } = this;

    // 绘制天球轮廓（上半球投影）
    ctx.beginPath();
    for (let az = 0; az <= 360; az += 2) {
      const pos = this.projectFromCenter(az, 0);
      if (pos.visible) {
        if (az === 0) {
          ctx.moveTo(pos.x, pos.y);
        } else {
          ctx.lineTo(pos.x, pos.y);
        }
      }
    }
    ctx.closePath();

    // 天球边缘光晕
    ctx.strokeStyle = 'rgba(100, 150, 255, 0.3)';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.strokeStyle = '#2D3748';
    ctx.lineWidth = 1;
    ctx.stroke();

    // 绘制高度角圈（营造球面深度感）
    const altitudes = [30, 60];
    altitudes.forEach(alt => {
      ctx.beginPath();
      for (let az = 0; az <= 360; az += 3) {
        const pos = this.projectFromCenter(az, alt);
        if (pos.visible) {
          if (az === 0) {
            ctx.moveTo(pos.x, pos.y);
          } else {
            ctx.lineTo(pos.x, pos.y);
          }
        }
      }
      ctx.closePath();
      ctx.strokeStyle = 'rgba(74, 85, 104, 0.3)';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }

  drawGrid() {
    const { ctx } = this;

    ctx.strokeStyle = 'rgba(74, 85, 104, 0.5)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // 高度角圈（3D球面投影）
    for (let alt = 30; alt <= 60; alt += 30) {
      ctx.beginPath();
      for (let az = 0; az <= 360; az += 2) {
        const pos = this.projectFromCenter(az, alt);
        if (pos.visible) {
          if (az === 0) {
            ctx.moveTo(pos.x, pos.y);
          } else {
            ctx.lineTo(pos.x, pos.y);
          }
        }
      }
      ctx.closePath();
      ctx.stroke();
    }

    // 方位角线（从天顶辐射到地平线）
    for (let az = 0; az < 360; az += 45) {
      ctx.beginPath();
      for (let alt = 0; alt <= 90; alt += 3) {
        const pos = this.projectFromCenter(az, alt);
        if (pos.visible) {
          if (alt === 0) {
            ctx.moveTo(pos.x, pos.y);
          } else {
            ctx.lineTo(pos.x, pos.y);
          }
        }
      }
      ctx.stroke();
    }

    ctx.setLineDash([]);

    // 绘制方位角标签（在靠近边缘的地方）
    const labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    labels.forEach((label, i) => {
      const az = i * 45;
      // 在靠近地平线但不是太近的位置
      const pos = this.projectFromCenter(az, 10);
      if (pos.visible) {
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, pos.x, pos.y);
      }
    });

    // 绘制高度角标签
    for (let alt = 30; alt <= 60; alt += 30) {
      const pos = this.projectFromCenter(0, alt);
      if (pos.visible) {
        ctx.fillStyle = '#94A3B8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${alt}°`, pos.x, pos.y);
      }
    }
  }

  drawHorizon() {
    const { ctx } = this;

    // 地平线（alt = 0，天空和大地的分界）
    ctx.beginPath();
    for (let az = 0; az <= 360; az += 1) {
      const pos = this.projectFromCenter(az, 0);
      if (pos.visible) {
        if (az === 0) {
          ctx.moveTo(pos.x, pos.y);
        } else {
          ctx.lineTo(pos.x, pos.y);
        }
      }
    }
    ctx.closePath();

    // 地平线渐变填充（表示大地）
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 地面半透明遮罩（在地平线下方）
    // 由于我们从中心向上看，地面在地平线以下
    // 不需要额外的遮罩，因为我们已经过滤了 y > 0 的目标
  }

  drawTargets() {
    const { ctx } = this;

    // 按照z轴排序（远到近）
    const sortedTargets = [...this.state.targets].sort((a, b) => {
      const posA = this.projectFromCenter(a.azimuth, a.altitude);
      const posB = this.projectFromCenter(b.azimuth, b.altitude);
      return posB.z - posA.z; // 远的先画（z小的先画）
    });

    sortedTargets.forEach(target => {
      const pos = this.projectFromCenter(target.azimuth, target.altitude);

      // 只渲染可见且在地平线以上的目标
      if (!pos.visible || target.altitude <= 0) return;

      const colors = {
        'emission-nebula': '#63B3ED',
        'galaxy': '#F687B3',
        'cluster': '#FBD38D',
        'planetary-nebula': '#6BCF7F',
        'supernova-remnant': '#A78BFA'
      };

      const color = colors[target.type] || '#FFFFFF';
      const isHovered = this.state.hoveredTarget === target.id;

      // 根据距离调整大小（近大远小）
      const baseSize = 8;
      const size = Math.max(3, Math.min(20, baseSize * pos.scale * 0.15));
      const hoverSize = size * 1.3;

      // 绘制光晕效果
      if (isHovered) {
        const gradient = ctx.createRadialGradient(
          pos.x, pos.y, 0,
          pos.x, pos.y, hoverSize * 2.5
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.4)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, hoverSize * 2.5, 0, Math.PI * 2);
        ctx.fill();
      }

      // 绘制目标本体
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isHovered ? hoverSize : size, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // 绘制边框
      ctx.strokeStyle = isHovered ? '#FFFFFF' : color;
      ctx.lineWidth = isHovered ? 2 : 1;
      ctx.stroke();

      // 绘制目标名称
      ctx.fillStyle = '#FFFFFF';
      ctx.font = isHovered ? 'bold 13px sans-serif' : '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(target.name || target.id, pos.x, pos.y - (isHovered ? hoverSize : size) - 4);

      // 悬停时显示详细信息
      if (isHovered) {
        const infoY = pos.y + (isHovered ? hoverSize : size) + 4;
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#94A3B8';

        // 显示高度角和方位角
        ctx.fillText(`${target.altitude.toFixed(1)}°`, pos.x, infoY);
        ctx.fillText(`${target.azimuth.toFixed(1)}°`, pos.x, infoY + 12);

        // 显示距离提示
        const distance = (this.config.radius - pos.z).toFixed(0);
        ctx.fillStyle = '#64748B';
        ctx.font = '10px sans-serif';
        ctx.fillText(`${distance}M`, pos.x, infoY + 24);
      }
    });
  }

  drawCompass() {
    const { ctx, config } = this;

    // 显示当前视角信息
    const text = `视角: ${this.view.azimuth.toFixed(0)}° ${this.view.altitude.toFixed(0)}°`;
    ctx.fillStyle = '#64748B';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'bottom';
    ctx.fillText(text, config.width - 20, config.height - 20);

    // 操作提示
    const hint = '拖动转头 | 滚轮缩放';
    ctx.textAlign = 'left';
    ctx.fillText(hint, 20, config.height - 20);

    // 天顶指示
    const zenithPos = this.projectFromCenter(0, 90);
    if (zenithPos.visible) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.font = '10px sans-serif';
      ctx.fillText('天顶', zenithPos.x, zenithPos.y - 15);
    }
  }

  handleHover(mouseX, mouseY) {
    let found = null;

    // 优先检测月球悬停
    if (this.state.moon.visible && this.state.moon.position) {
      if (this.isPointOnMoon(mouseX, mouseY)) {
        this.state.moon.hovered = true;
        this.canvas.style.cursor = 'pointer';
        this.render();
        return;
      } else if (this.state.moon.hovered) {
        this.state.moon.hovered = false;
      }
    }

    // 检测是否悬停在目标上
    for (const target of this.state.targets) {
      const pos = this.projectFromCenter(target.azimuth, target.altitude);

      if (!pos.visible || target.altitude <= 0) continue;

      const baseSize = 8 * pos.scale * 0.15;
      const size = Math.max(3, Math.min(20, baseSize));

      const distance = Math.sqrt(
        Math.pow(mouseX - pos.x, 2) +
        Math.pow(mouseY - pos.y, 2)
      );

      if (distance < size + 5) {
        found = target.id;
        break;
      }
    }

    this.state.hoveredTarget = found;
    this.canvas.style.cursor = found ? 'pointer' : (this.state.isDragging ? 'grabbing' : 'grab');
    this.render();
  }

  handleClick(x, y) {
    if (!this.state.isDragging && !this.state.fovFrame.isDragging) {
      // 优先检测月球点击
      if (this.state.moon.visible && this.isPointOnMoon(x, y)) {
        this.state.moon.selected = !this.state.moon.selected;
        this.onMoonSelect?.(this.state.moon);
        this.render();
        return;
      }

      // 检测目标点击
      if (this.state.hoveredTarget) {
        this.onTargetSelect?.(this.state.hoveredTarget);
      }
    }
  }

  updateData(data) {
    this.state = { ...this.state, ...data };
    this.render();
  }

  /**
   * 设置 FOV 框中心位置
   * @param {number} azimuth - 方位角（度）
   * @param {number} altitude - 高度角（度）
   */
  setFOVFrameCenter(azimuth, altitude) {
    this.state.fovFrame.center = {
      azimuth: (azimuth + 360) % 360,
      altitude: Math.max(0, Math.min(90, altitude))
    };
    this.render();
  }

  /**
   * 设置 FOV 框可见性
   * @param {boolean} visible - 是否可见
   */
  setFOVFrameVisible(visible) {
    this.state.fovFrame.isVisible = visible;
    this.render();
  }

  /**
   * 更新 FOV 框大小（设备变化时调用）
   * @param {number} fovH - 水平视野角（度）
   * @param {number} fovV - 垂直视野角（度）
   */
  updateFOVFrameSize(fovH, fovV) {
    // 保存到 config 中供绘制使用
    this.config.fovHorizontal = fovH;
    this.config.fovVertical = fovV;
    this.render();
  }

  /**
   * 设置视角（原地转头）
   * @param {number} azimuth - 方位角（度）
   * @param {number} altitude - 高度角（度）
   */
  setView(azimuth, altitude) {
    this.view.azimuth = azimuth;
    this.view.altitude = Math.max(0, Math.min(90, altitude));
    this.render();
  }

  /**
   * 重置视角
   */
  resetView() {
    this.view.azimuth = 0;
    this.view.altitude = 0;  // 平视地平线
    this.view.zoom = 1.0;
    this.render();
  }

  /**
   * 绘制可视区域
   */
  drawVisibleZones() {
    const { ctx } = this;

    if (!this.state.zones || this.state.zones.length === 0) return;

    this.state.zones.forEach(zone => {
      if (zone.type === 'rectangle') {
        this.drawRectZone(zone);
      }
    });
  }

  /**
   * 绘制矩形区域
   * @param {Object} zone - 区域对象 {id, name, type, start, end, isDefault}
   */
  drawRectZone(zone) {
    const { ctx } = this;
    const [startAz, startAlt] = zone.start;
    const [endAz, endAlt] = zone.end;

    // 矩形的四个顶点
    const corners = [
      [startAz, startAlt],  // 左下
      [endAz, startAlt],    // 右下
      [endAz, endAlt],      // 右上
      [startAz, endAlt]     // 左上
    ];

    // 投影到屏幕坐标
    const projected = corners.map(([az, alt]) =>
      this.projectFromCenter(az, alt)
    );

    // 过滤不可见顶点
    const visible = projected.filter(p => p.visible);
    if (visible.length < 2) return;

    // 绘制半透明填充
    ctx.beginPath();
    ctx.moveTo(visible[0].x, visible[0].y);
    for (let i = 1; i < visible.length; i++) {
      ctx.lineTo(visible[i].x, visible[i].y);
    }
    ctx.closePath();

    ctx.fillStyle = zone.isDefault
      ? 'rgba(100, 116, 139, 0.1)'
      : 'rgba(239, 68, 68, 0.15)';
    ctx.fill();

    // 绘制边框
    ctx.strokeStyle = zone.isDefault
      ? 'rgba(148, 163, 184, 0.3)'
      : 'rgba(239, 68, 68, 0.5)';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);

    // 绘制区域名称
    if (!zone.isDefault) {
      const center = this.projectFromCenter(
        (startAz + endAz) / 2,
        (startAlt + endAlt) / 2
      );

      if (center.visible) {
        ctx.fillStyle = 'rgba(239, 68, 68, 0.8)';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(zone.name, center.x, center.y);
      }
    }
  }

  /**
   * 绘制 FOV 框
   */
  drawFOVFrame() {
    const { ctx } = this;
    const { fovFrame } = this.state;

    // 不显示或没有 FOV 数据时跳过
    if (!fovFrame.isVisible || !this.config.fovHorizontal) return;

    const { center } = fovFrame;
    const fovH = this.config.fovHorizontal / 2;  // 半宽
    const fovV = this.config.fovVertical / 2;    // 半高

    // 计算矩形四个角（相对于中心）
    const corners = [
      [center.azimuth - fovH, center.altitude - fovV],  // 左下
      [center.azimuth + fovH, center.altitude - fovV],  // 右下
      [center.azimuth + fovH, center.altitude + fovV],  // 右上
      [center.azimuth - fovH, center.altitude + fovV]   // 左上
    ];

    // 处理方位角跨越 0/360 度的情况
    const normalizedCorners = corners.map(([az, alt]) => [
      ((az % 360) + 360) % 360,
      Math.max(0, alt)
    ]);

    // 投影到屏幕坐标
    const projected = normalizedCorners.map(([az, alt]) =>
      this.projectFromCenter(az, alt)
    );

    // 过滤不可见顶点
    const visible = projected.filter(p => p.visible);
    if (visible.length < 3) return;

    // 绘制半透明填充
    ctx.beginPath();
    ctx.moveTo(visible[0].x, visible[0].y);
    for (let i = 1; i < visible.length; i++) {
      ctx.lineTo(visible[i].x, visible[i].y);
    }
    ctx.closePath();

    // 选中状态更亮
    if (fovFrame.isSelected) {
      ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.9)';
      ctx.lineWidth = 3;
    } else {
      ctx.fillStyle = 'rgba(59, 130, 246, 0.15)';
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)';
      ctx.lineWidth = 2;
    }

    ctx.fill();
    ctx.stroke();

    // 绘制中心点
    const centerPos = this.projectFromCenter(center.azimuth, center.altitude);
    if (centerPos.visible) {
      // 中心点标记
      ctx.beginPath();
      ctx.arc(centerPos.x, centerPos.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = fovFrame.isSelected ? '#FFFFFF' : 'rgba(255, 255, 255, 0.8)';
      ctx.fill();

      // 中心十字
      ctx.beginPath();
      ctx.moveTo(centerPos.x - 4, centerPos.y);
      ctx.lineTo(centerPos.x + 4, centerPos.y);
      ctx.moveTo(centerPos.x, centerPos.y - 4);
      ctx.lineTo(centerPos.x, centerPos.y + 4);
      ctx.strokeStyle = '#3B82F6';
      ctx.lineWidth = 2;
      ctx.stroke();

      // 显示坐标信息
      if (fovFrame.isSelected || fovFrame.isDragging) {
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(
          `FOV: ${this.config.fovHorizontal.toFixed(1)}° × ${this.config.fovVertical.toFixed(1)}°`,
          centerPos.x,
          centerPos.y - 12
        );

        ctx.font = '11px sans-serif';
        ctx.textBaseline = 'top';
        ctx.fillText(
          `${center.altitude.toFixed(1)}° ${center.azimuth.toFixed(1)}°`,
          centerPos.x,
          centerPos.y + 12
        );
      }
    }
  }

  /**
   * 检测点是否在 FOV 框内
   * @param {number} x - 屏幕坐标 X
   * @param {number} y - 屏幕坐标 Y
   * @returns {boolean}
   */
  isPointInFOVFrame(x, y) {
    const { fovFrame } = this.state;
    if (!fovFrame.isVisible || !this.config.fovHorizontal) return false;

    const { center } = fovFrame;
    const fovH = this.config.fovHorizontal / 2;
    const fovV = this.config.fovVertical / 2;

    // 计算矩形边界
    const minAz = ((center.azimuth - fovH) % 360 + 360) % 360;
    const maxAz = ((center.azimuth + fovH) % 360 + 360) % 360;
    const minAlt = Math.max(0, center.altitude - fovV);
    const maxAlt = Math.min(90, center.altitude + fovV);

    // 采样检测：在矩形内采样多个点，检测屏幕坐标
    const samples = 9;
    for (let i = 0; i < samples; i++) {
      for (let j = 0; j < samples; j++) {
        const az = minAz + (maxAz - minAz) * (i / (samples - 1));
        const alt = minAlt + (maxAlt - minAlt) * (j / (samples - 1));
        const pos = this.projectFromCenter(az, alt);

        if (pos.visible) {
          const dist = Math.sqrt(Math.pow(x - pos.x, 2) + Math.pow(y - pos.y, 2));
          if (dist < 15) return true;  // 阈值 15 像素
        }
      }
    }

    return false;
  }

  /**
   * 绘制月球
   */
  drawMoon() {
    const { ctx } = this;
    const { moon } = this.state;

    // 如果没有月球数据或不可见，跳过
    if (!moon.visible || !moon.position) return;

    const pos = this.projectFromCenter(moon.position.azimuth, moon.position.altitude);

    // 只渲染可见且在地平线以上的月球
    if (!pos.visible || moon.position.altitude <= 0) return;

    // 保存月球屏幕位置供后续使用
    moon.screenX = pos.x;
    moon.screenY = pos.y;

    const baseSize = 20;
    const size = Math.max(10, Math.min(40, baseSize * pos.scale * 0.2));
    const isHovered = moon.hovered;
    const isSelected = moon.selected;
    const moonSize = isHovered || isSelected ? size * 1.3 : size;

    // 绘制光晕效果
    if (isHovered || isSelected) {
      const gradient = ctx.createRadialGradient(
        pos.x, pos.y, 0,
        pos.x, pos.y, moonSize * 2.5
      );
      gradient.addColorStop(0, 'rgba(255, 255, 200, 0.5)');
      gradient.addColorStop(1, 'rgba(255, 255, 200, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, moonSize * 2.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // 绘制月球本体（圆）
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, moonSize, 0, Math.PI * 2);

    // 月球颜色（根据月相）
    const illumination = moon.phase ? moon.phase.percentage / 100 : 50;
    const brightness = Math.floor(180 + illumination * 75);
    ctx.fillStyle = `rgb(${brightness}, ${brightness}, ${brightness - 30})`;
    ctx.fill();

    // 绘制月球边框
    ctx.strokeStyle = isSelected ? '#FFFFFF' : `rgb(${brightness - 30}, ${brightness - 30}, ${brightness - 60})`;
    ctx.lineWidth = isSelected ? 3 : 1;
    ctx.stroke();

    // 绘制月相（新月显示为月牙，满月显示为满圆）
    if (moon.phase) {
      this.drawMoonPhase(ctx, pos.x, pos.y, moonSize, moon.phase);
    }

    // 绘制月球标签
    ctx.fillStyle = '#FFFFFF';
    ctx.font = isHovered || isSelected ? 'bold 13px sans-serif' : '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText('月球', pos.x, pos.y - moonSize - 4);

    // 悬停或选中时显示详细信息
    if (isHovered || isSelected) {
      this.drawMoonTooltip(ctx, pos, moonSize, moon);
    }
  }

  /**
   * 绘制月相
   * @param {CanvasRenderingContext2D} ctx - Canvas context
   * @param {number} x - Center X
   * @param {number} y - Center Y
   * @param {number} size - Moon radius
   * @param {Object} phase - Phase data { name, percentage, age_days }
   */
  drawMoonPhase(ctx, x, y, size, phase) {
    const percentage = phase.percentage;

    // 新月到上弦月（右侧亮）
    if (percentage < 50) {
      this.drawMoonCrescent(ctx, x, y, size, percentage, 'right');
    }
    // 上弦月到满月（右侧全亮，左侧逐渐变亮）
    else if (percentage === 50) {
      // 上弦月：右半圆亮
      ctx.beginPath();
      ctx.arc(x, y, size, -Math.PI / 2, Math.PI / 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fill();
    }
    // 满月（全亮）
    else if (percentage === 100) {
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fill();
    }
    // 满月到下弦月（左侧逐渐变暗）
    else if (percentage > 50 && percentage < 100) {
      const darkness = (percentage - 50) / 50; // 0 to 1
      ctx.beginPath();
      ctx.arc(x, y, size, Math.PI / 2, -Math.PI / 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fill();

      // 左侧阴影
      ctx.beginPath();
      ctx.arc(x + size * darkness, y, size, -Math.PI / 2, Math.PI / 2);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
      ctx.fill();
    }
    // 下弦月到新月（左侧亮）
    else {
      this.drawMoonCrescent(ctx, x, y, size, 100 - percentage, 'left');
    }
  }

  /**
   * 绘制月牙（新月或残月）
   * @param {CanvasRenderingContext2D} ctx - Canvas context
   * @param {number} x - Center X
   * @param {number} y - Center Y
   * @param {number} size - Moon radius
   * @param {number} percentage - Illumination percentage (0-50)
   * @param {string} side - 'right' or 'left'
   */
  drawMoonCrescent(ctx, x, y, size, percentage, side) {
    const offset = size * (1 - percentage / 50);

    ctx.save();

    // 创建月球剪切路径
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.clip();

    // 绘制亮部
    ctx.beginPath();
    if (side === 'right') {
      ctx.arc(x, y, size, -Math.PI / 2, Math.PI / 2);
      ctx.arc(x + offset, y, size, Math.PI / 2, -Math.PI / 2);
    } else {
      ctx.arc(x, y, size, Math.PI / 2, -Math.PI / 2);
      ctx.arc(x - offset, y, size, -Math.PI / 2, Math.PI / 2);
    }
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fill();

    ctx.restore();
  }

  /**
   * 绘制月球提示框
   * @param {CanvasRenderingContext2D} ctx - Canvas context
   * @param {Object} pos - Projected position { x, y, z, visible, scale }
   * @param {number} size - Moon size
   * @param {Object} moon - Moon state
   */
  drawMoonTooltip(ctx, pos, size, moon) {
    const infoY = pos.y + size + 8;
    const lineHeight = 14;

    // 半透明背景
    const padding = 8;
    const boxWidth = 140;
    const boxHeight = moon.phase ? lineHeight * 4 + padding * 2 : lineHeight * 3 + padding * 2;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(pos.x - boxWidth / 2, infoY, boxWidth, boxHeight);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 1;
    ctx.strokeRect(pos.x - boxWidth / 2, infoY, boxWidth, boxHeight);

    // 绘制信息
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    let y = infoY + padding;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(`高度: ${moon.position.altitude.toFixed(1)}°`, pos.x, y);
    y += lineHeight;

    ctx.fillText(`方位: ${moon.position.azimuth.toFixed(1)}°`, pos.x, y);
    y += lineHeight;

    if (moon.phase) {
      ctx.fillStyle = '#FFD700';
      ctx.fillText(`${moon.phase.name} (${moon.phase.percentage.toFixed(0)}%)`, pos.x, y);
      y += lineHeight;
    }

    ctx.fillStyle = '#94A3B8';
    ctx.font = '10px sans-serif';
    const distance = (moon.position.distance || 384400).toFixed(0);
    ctx.fillText(`距离: ${Number(distance).toLocaleString()} km`, pos.x, y);
  }

  /**
   * 检测点是否在月球上
   * @param {number} x - Screen X
   * @param {number} y - Screen Y
   * @returns {boolean}
   */
  isPointOnMoon(x, y) {
    const { moon } = this.state;

    if (!moon.visible || !moon.position || moon.screenX === undefined) return false;

    const baseSize = 20;
    const pos = this.projectFromCenter(moon.position.azimuth, moon.position.altitude);
    const size = Math.max(10, Math.min(40, baseSize * pos.scale * 0.2));
    const moonSize = moon.hovered || moon.selected ? size * 1.3 : size;

    const distance = Math.sqrt(
      Math.pow(x - moon.screenX, 2) +
      Math.pow(y - moon.screenY, 2)
    );

    return distance < moonSize + 5;
  }
}
