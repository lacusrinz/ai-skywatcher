# 设备视野框 (FOV Frame) 功能开发进度

**日期**: 2025-01-24
**版本**: v2.4.0
**功能**: 在天空图中显示并交互设备视野框

---

## 概述

实现了一个可视化的设备视野框（FOV Frame）功能，允许用户在天空图上查看相机的视野范围，并通过拖动来规划拍摄构图。该功能与设备配置集成，支持自定义设备尺寸和预设切换。

---

## 核心功能

### 1. FOV 框显示
- 基于 `currentEquipment` 的 fov_horizontal 和 fov_vertical 在天球上绘制矩形框
- 使用蓝色半透明样式，未选中时透明度 15%，选中时 30%
- 中心点标记为白色圆点带蓝色十字
- 选中/拖动时显示 FOV 尺寸和中心坐标信息

### 2. 交互功能
- **点击高亮**: 鼠标悬停时自动高亮，点击后保持高亮状态
- **拖动定位**: 拖动 FOV 框改变其中心位置（方位角、高度角）
- **事件优先级**: FOV 框拖动优先于视角拖动
- **碰撞检测**: 使用 9x9 采样检测法，适合投影变形场景

### 3. 设备集成
- 设备预设切换时自动更新 FOV 框大小
- 自定义设备配置时实时更新 FOV
- FOV 尺寸与传感器尺寸、焦距联动

### 4. 状态持久化
- FOV 框位置保存到 localStorage
- 刷新页面后位置恢复
- 默认位置：方位角 180°，高度角 45°

### 5. UI 控件
- 显示/隐藏开关（复选框）
- 重置位置按钮（恢复到默认 180°, 45°）
- 防抖保存（500ms）减少 localStorage 写入

---

## 技术实现

### 文件修改清单

#### 1. `frontend/src/scripts/utils/canvas.js`

**新增状态**:
```javascript
fovFrame: {
  center: { azimuth: 180, altitude: 45 },
  isVisible: true,
  isSelected: false,
  isDragging: false
}
```

**新增方法**:
- `setFOVFrameCenter(azimuth, altitude)` - 设置中心位置
- `setFOVFrameVisible(visible)` - 切换可见性
- `updateFOVFrameSize(fovH, fovV)` - 更新尺寸
- `drawFOVFrame()` - 绘制 FOV 框
- `isPointInFOVFrame(x, y)` - 碰撞检测

**修改方法**:
- `bindEvents()` - 添加 FOV 框事件处理
- `render()` - 添加 `drawFOVFrame()` 调用

#### 2. `frontend/src/scripts/utils/storage.js`

**新增存储键**:
- `FOV_FRAME_POSITION: 'skywatcher_fov_frame_position'`

**新增函数**:
- `getFOVFramePosition()` - 获取保存的位置
- `saveFOVFramePosition(position)` - 保存位置

#### 3. `frontend/src/scripts/main.js`

**新增函数**:
- `initFOVFrame()` - 初始化 FOV 框（加载位置、设置尺寸、绑定回调）

**修改函数**:
- `handleEquipmentPresetChange()` - 切换预设时更新 FOV 尺寸
- `calculateFOVFromInput()` - 自定义设备时更新 FOV 尺寸
- `initApp()` - 添加 `initFOVFrame()` 调用
- `setupEventListeners()` - 添加 FOV 控件事件监听

**新增导入**:
- `getFOVFramePosition, saveFOVFramePosition`

#### 4. `frontend/src/index.html`

**新增元素**:
```html
<div class="fov-controls">
  <label class="checkbox-label">
    <input type="checkbox" id="chkShowFOV" checked>
    <span>显示视野框 (FOV)</span>
  </label>
  <button class="btn-secondary" id="btnResetFOV">重置位置</button>
</div>
```

#### 5. `frontend/src/styles/components.css`

**新增样式**:
- `.fov-controls` - FOV 控制容器
- `.checkbox-label` - 复选框标签样式
- `.checkbox-label input[type="checkbox"]` - 复选框样式

---

## 数据流

```
用户操作
    ↓
Canvas 事件 (mousedown/mousemove/mouseup)
    ↓
isPointInFOVFrame() 碰撞检测
    ↓
更新 fovFrame.center
    ↓
drawFOVFrame() 重新绘制
    ↓
onFOVFrameMove 回调（防抖 500ms）
    ↓
saveFOVFramePosition() 保存到 localStorage
```

```
设备配置变化
    ↓
handleEquipmentPresetChange() / calculateFOVFromInput()
    ↓
更新 currentEquipment
    ↓
skyMap.updateFOVFrameSize(fovH, fovV)
    ↓
drawFOVFrame() 重新绘制
```

---

## 关键技术点

### 1. 3D 投影复用
- 复用 `projectFromCenter()` 方法进行天球坐标到屏幕坐标的转换
- 保持与现有可视区域、目标绘制一致的投影系统

### 2. 采样检测法
```javascript
// 在矩形内采样 9x9 个点
for (let i = 0; i < samples; i++) {
  for (let j = 0; j < samples; j++) {
    const pos = this.projectFromCenter(az, alt);
    const dist = Math.sqrt(Math.pow(x - pos.x, 2) + Math.pow(y - pos.y, 2));
    if (dist < 15) return true;
  }
}
```
- 适合投影变形场景
- 阈值 15 像素，提高点击体验

### 3. 事件优先级
```javascript
// mousedown: FOV 框优先
if (this.isPointInFOVFrame(x, y)) {
  // FOV 框拖动
  return;
}
// 视角拖动

// mousemove: FOV 框优先
if (this.state.fovFrame.isDragging) {
  // FOV 框拖动
  return;
}
// 视角拖动
```

### 4. 防抖保存
```javascript
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

skyMap.onFOVFrameMove = debounce((center) => {
  saveFOVFramePosition(center);
}, 500);
```
- 减少 localStorage 写入频率
- 提升性能

### 5. 坐标边界处理
```javascript
// 方位角归一化（0-360°）
azimuth: (azimuth + 360) % 360

// 高度角限制（0-90°）
altitude: Math.max(0, Math.min(90, altitude))
```

---

## 使用说明

### 基本操作
1. **查看 FOV 框**: FOV 框默认显示为蓝色半透明矩形
2. **选中高亮**: 鼠标悬停在 FOV 框上会自动高亮
3. **拖动定位**: 点击并拖动 FOV 框改变拍摄方向
4. **查看信息**: 选中或拖动时显示 FOV 尺寸和中心坐标

### 设备切换
1. 在左侧配置面板选择不同的设备预设
2. FOV 框自动更新大小
3. 位置保持不变

### 自定义设备
1. 选择"自定义"预设
2. 输入传感器尺寸和焦距
3. FOV 框自动计算并更新

### 控制按钮
- **显示/隐藏**: 使用复选框切换 FOV 框显示
- **重置位置**: 点击"重置位置"按钮恢复到默认位置（180°, 45°）

---

## 测试验证

### 功能测试
- ✅ FOV 框正确显示在默认位置 (180°, 45°)
- ✅ FOV 框尺寸与设备配置匹配
- ✅ 点击 FOV 框时高亮显示
- ✅ 拖动时中心坐标实时更新
- ✅ 拖动到边界（alt=0°, alt=90°）正确限制
- ✅ 方位角跨越 0°/360° 正确处理

### 集成测试
- ✅ 切换设备预设时 FOV 框大小自动更新
- ✅ 自定义设备时 FOV 框大小自动更新
- ✅ 刷新页面后 FOV 框位置恢复
- ✅ 显示/隐藏开关正确工作
- ✅ 重置按钮将 FOV 框移回默认位置

### 边界测试
- ✅ 最小 FOV（鱼眼镜头）
- ✅ 最大 FOV（广角镜头）
- ✅ FOV 框中心接近地平线 (alt ≈ 0°)
- ✅ FOV 框中心接近天顶 (alt ≈ 90°)
- ✅ FOV 框跨越方位角 0°/360°

---

## 后续优化建议

### 功能增强
1. **多 FOV 框**: 支持同时显示多个设备的 FOV（对比不同镜头）
2. **FOV 对齐**: 自动对齐到网格或目标
3. **预设位置**: 保存常用的 FOV 位置（如银河中心、M42 等）
4. **时间轴联动**: FOV 框随时间轴移动显示目标路径

### 交互优化
1. **快捷键**: 键盘快捷键调整 FOV 位置
2. **精确定位**: 输入精确坐标定位 FOV
3. **目标捕捉**: 拖动时自动吸附到附近的天体目标

### 视觉增强
1. **FOV 预览**: 显示 FOV 内的目标缩略图
2. **构图辅助**: 显示三分线、黄金分割等构图辅助线
3. **目标高亮**: FOV 内的目标特殊标记

---

## 已知限制

1. **单次投影**: 当前使用球面-平面投影，边缘可能有变形
2. **固定采样**: 碰撞检测使用 9x9 采样，极小 FOV 可能不够精确
3. **无旋转**: FOV 框不能旋转（相机传感器角度固定）

---

## 构建验证

```bash
cd D:\Coding\ai-skywatcher\frontend
npm run build
```

**构建结果**:
```
✓ 11 modules transformed
../dist/index.html          9.90 kB │ gzip: 2.96 kB
../dist/assets/main-*.css  16.56 kB │ gzip: 3.41 kB
../dist/assets/main-*.js   32.44 kB │ gzip: 10.08 kB
✓ built in 94ms
```

构建成功，无错误。

---

## 总结

成功实现了设备视野框（FOV Frame）功能，为用户提供了直观的拍摄构图工具。该功能与现有设备配置系统无缝集成，支持拖动交互和状态持久化，大大提升了用户规划天文摄影的便利性。

**开发时间**: 约 3 小时
**代码质量**: 通过构建验证，无错误
**用户体验**: 流畅的交互，清晰的视觉反馈
