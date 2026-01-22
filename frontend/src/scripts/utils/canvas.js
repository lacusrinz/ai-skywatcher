// Sky Map Canvas
export class SkyMapCanvas {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.config = {
      width: 800,
      height: 800,
      centerX: 400,
      centerY: 400,
      maxRadius: 380,
      ...options
    };

    this.state = {
      time: new Date(),
      targets: [],
      zones: [],
      hoveredTarget: null,
      zoom: 1.0,
      pan: { x: 0, y: 0 }
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
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this.handleMouseMove(x, y);
    });

    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      this.handleClick(x, y);
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.handleZoom(e.deltaY);
    });
  }

  render() {
    const { ctx, config, state } = this;

    ctx.clearRect(0, 0, config.width, config.height);

    this.drawBackground();
    this.drawGrid();
    this.drawVisibleZones();
    this.drawTargets();
    this.drawHorizon();
  }

  drawBackground() {
    const { ctx, config } = this;

    const gradient = ctx.createRadialGradient(
      config.centerX, config.centerY, 0,
      config.centerX, config.centerY, config.maxRadius
    );
    gradient.addColorStop(0, '#1A1A2E');
    gradient.addColorStop(1, '#0F172A');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, config.width, config.height);
  }

  drawGrid() {
    const { ctx, config } = this;

    ctx.strokeStyle = '#4A5568';
    ctx.lineWidth = 1;

    // Altitude circles
    for (let alt of [15, 30, 45, 60, 75, 90]) {
      const radius = (alt / 90) * config.maxRadius;
      ctx.beginPath();
      ctx.arc(config.centerX, config.centerY, radius, 0, Math.PI * 2);
      ctx.stroke();

      ctx.fillStyle = '#94A3B8';
      ctx.font = '12px sans-serif';
      ctx.fillText(`${alt}°`, config.centerX + 5, config.centerY - radius + 15);
    }

    // Azimuth lines
    for (let az of [0, 45, 90, 135, 180, 225, 270, 315]) {
      const angle = (az - 90) * (Math.PI / 180);
      const x = config.centerX + Math.cos(angle) * config.maxRadius;
      const y = config.centerY + Math.sin(angle) * config.maxRadius;

      ctx.beginPath();
      ctx.moveTo(config.centerX, config.centerY);
      ctx.lineTo(x, y);
      ctx.stroke();

      const labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '14px sans-serif';
      ctx.fillText(
        labels[az / 45],
        x + Math.cos(angle) * 20 - 10,
        y + Math.sin(angle) * 20 + 5
      );
    }
  }

  drawHorizon() {
    const { ctx, config } = this;

    ctx.strokeStyle = '#2D3748';
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.arc(config.centerX, config.centerY, config.maxRadius, 0, Math.PI * 2);
    ctx.stroke();
  }

  drawTargets() {
    const { ctx, config, state } = this;

    state.targets.forEach(target => {
      const pos = this.azAltToXY(target.azimuth, target.altitude);

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);

      const colors = {
        'emission-nebula': '#63B3ED',
        'galaxy': '#F687B3',
        'cluster': '#FBD38D'
      };
      ctx.fillStyle = colors[target.type] || '#FFFFFF';
      ctx.fill();

      if (state.hoveredTarget === target.id) {
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });
  }

  drawVisibleZones() {
    const { ctx, config, state } = this;

    state.zones.forEach(zone => {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.5)';
      ctx.lineWidth = 2;

      ctx.beginPath();
      zone.polygon.forEach(([az, alt], i) => {
        const pos = this.azAltToXY(az, alt);
        if (i === 0) {
          ctx.moveTo(pos.x, pos.y);
        } else {
          ctx.lineTo(pos.x, pos.y);
        }
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }

  azAltToXY(azimuth, altitude) {
    const { config } = this;
    const radius = (altitude / 90) * config.maxRadius;
    const angle = (azimuth - 90) * (Math.PI / 180);

    return {
      x: config.centerX + Math.cos(angle) * radius,
      y: config.centerY + Math.sin(angle) * radius
    };
  }

  xyToAzAlt(x, y) {
    const { config } = this;
    const dx = x - config.centerX;
    const dy = y - config.centerY;
    const radius = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI) + 90;

    return {
      azimuth: (angle + 360) % 360,
      altitude: Math.min(90, (radius / config.maxRadius) * 90)
    };
  }

  handleMouseMove(x, y) {
    const pos = this.xyToAzAlt(x, y);

    const hoveredTarget = this.state.targets.find(target => {
      const targetPos = this.azAltToXY(target.azimuth, target.altitude);
      const distance = Math.sqrt(Math.pow(x - targetPos.x, 2) + Math.pow(y - targetPos.y, 2));
      return distance < 10;
    });

    if (hoveredTarget) {
      this.canvas.style.cursor = 'pointer';
    } else {
      this.canvas.style.cursor = 'default';
    }

    this.state.hoveredTarget = hoveredTarget ? hoveredTarget.id : null;
    this.render();
  }

  handleClick(x, y) {
    if (this.state.hoveredTarget) {
      this.onTargetSelect?.(this.state.hoveredTarget);
    }
  }

  handleZoom(delta) {
    const zoomFactor = delta > 0 ? 0.9 : 1.1;
    this.state.zoom = Math.max(0.5, Math.min(2.0, this.state.zoom * zoomFactor));
    this.render();
  }

  updateData(data) {
    this.state = { ...this.state, ...data };
    this.render();
  }
}
