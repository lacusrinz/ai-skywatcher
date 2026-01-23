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
      lastMouseY: 0
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
      this.state.isDragging = true;
      this.state.lastMouseX = e.clientX;
      this.state.lastMouseY = e.clientY;
      this.canvas.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
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
      this.state.isDragging = false;
      this.canvas.style.cursor = 'grab';
    });

    // 悬停检测
    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.state.isDragging) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        this.handleHover(x, y);
      }
    });

    // 点击选择
    this.canvas.addEventListener('click', (e) => {
      if (this.state.hoveredTarget && !this.state.isDragging) {
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
    if (this.state.hoveredTarget && !this.state.isDragging) {
      this.onTargetSelect?.(this.state.hoveredTarget);
    }
  }

  updateData(data) {
    this.state = { ...this.state, ...data };
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
}
