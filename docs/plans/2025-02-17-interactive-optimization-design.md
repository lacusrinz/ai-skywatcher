# 交互优化设计文档

**Date**: 2025-02-17
**Status**: Design Phase
**Author**: AI Skywatcher Team

---

## Overview

本文档描述了两项关键交互优化功能的设计方案，旨在提升用户体验和决策效率：

1. **点击推荐卡片对焦+高亮**：点击推荐列表中的天体卡片，天空图自动对焦到该天体并显示高亮动画
2. **FOV 框叠加天体大小**：拖动 FOV 框到天体上时，显示天体真实大小在设备视场中的占比

---

## 功能 1：点击推荐卡片对焦 + 高亮

### 目标

当用户点击推荐面板中的天体卡片时，天空图自动调整视角将目标天体移至视野中心，并播放脉冲高亮动画，帮助用户快速定位和理解目标位置。

### 用户流程

```
用户点击推荐卡片
    ↓
天空图平滑旋转到目标方向（600ms）
    ↓
到达目标后，天体显示脉冲高亮动画（1.5秒）
    ↓
用户可以清晰看到目标在天空中的位置
```

### 技术实现

#### 架构

```
main.js: handleTargetClick(targetId)
    ↓
查找推荐数据中的目标信息
    ↓
skyMap.focusOnTarget(target, options)
    ├─ 计算目标视角（azimuth, altitude）
    ├─ 启动平滑动画（requestAnimationFrame）
    │   └─ 使用 easeInOutCubic 缓动
    └─ 动画完成后触发
         ↓
skyMap.highlightTarget(targetId)
    └─ 脉冲动画（1.5秒，3次跳动）
```

#### 核心方法

**`SkyMapCanvas.focusOnTarget(target, options)`**

- **参数**：
  - `target`: { azimuth, altitude, id, name }
  - `options`: { duration, elevation, onComplete }
- **行为**：
  - 计算目标视角（高度角上抬 10-15° 以获得更好视角）
  - 使用 `requestAnimationFrame` 实现平滑过渡
  - 使用 `easeInOutCubic` 缓动函数
  - 动画时长：600ms（可配置）

**`SkyMapCanvas.animateFocus(timestamp)`**

- 插值计算当前视角
- 处理方位角 0°/360° 边界问题
- 动画完成后调用 `onComplete` 回调

**`SkyMapCanvas.highlightTarget(targetId)`**

- 设置 `state.highlightedTarget`
- 使用正弦波实现脉冲效果（1.5秒，3次跳动）
- 动画结束后清除状态

**`SkyMapCanvas.drawTargets()` 修改**

- 检测 `state.highlightedTarget`
- 绘制两层同心圆（外圈+内圈）
- 使用动态透明度实现脉冲效果

#### 集成点

**文件**: `frontend/src/scripts/main.js`

- 修改推荐卡片点击事件处理器（约 723-729 行）
- 调用 `skyMap.focusOnTarget()` 传递目标位置
- 在 `onComplete` 回调中调用 `skyMap.highlightTarget()`
- 保存 `window.currentRecommendations` 供点击事件访问

#### 视觉效果

- **对焦动画**：600ms 平滑旋转，使用缓动函数
- **高亮效果**：外圈脉冲（0.8倍大小）+ 内圈高亮（0.6倍大小）
- **颜色**：白色半透明（rgba(255,255,255,0.3-0.7)）

---

## 功能 2：FOV 框叠加天体大小

### 目标

当用户拖动设备 FOV 框到某个天体上时，在天空图上显示该天体的真实大小（相对于 FOV 的占比），帮助用户直观判断该天体是否适合当前设备拍摄。

### 用户流程

```
用户拖动 FOV 框
    ↓
系统检测 FOV 框中心附近的天体
    ↓
如果找到天体（阈值：FOV 对角线 50%）
    ↓
绘制天体真实大小轮廓（虚线圆圈）
    ↓
显示天体名称、大小、占 FOV 百分比
    ↓
根据占比显示颜色编码：
  - 绿色：< 20%（合适）
  - 黄色：20-50%（适中）
  - 红色：> 50%（过大）
```

### 技术实现

#### 架构

```
用户拖动 FOV 框
    ↓
每次重绘时调用 checkFovTargetOverlap()
    ├─ 获取 FOV 框中心在 Canvas 上的位置
    ├─ 遍历所有天体，找到最近的天体
    └─ 计算天体大小与 FOV 的比例
         ↓
drawFovTargetOverlay()
    ├─ 绘制虚线圆圈表示天体真实大小
    ├─ 根据占比设置颜色（绿/黄/红）
    └─ 显示文本标签和匹配度提示
```

#### 核心方法

**`SkyMapCanvas.checkFovTargetOverlap()`**

- **返回值**：{ target, overlapPercentage, canvasSize, distance } 或 null
- **逻辑**：
  1. 获取 FOV 框中心在 Canvas 上的坐标
  2. 计算阈值距离（FOV 尺寸的 50%）
  3. 遍历所有天体，找到距离中心最近的天体
  4. 计算天体占 FOV 对角线的百分比
  5. 返回目标信息和占比

**`SkyMapCanvas.getFovPixelSize()`**

- **返回值**：{ width, height } 单位：像素
- **逻辑**：
  - 从 `window.currentEquipment` 获取当前设备 FOV
  - 将角度（度）转换为 Canvas 像素
  - 使用线性映射：90° 对应 `config.radius * 2`

**`SkyMapCanvas.calculateTargetFovRatio(target)`**

- **返回值**：{ overlapPercentage, canvasSize }
- **逻辑**：
  - 将 `target.size`（角分）转换为角度
  - 计算天体与 FOV 对角线的比例
  - 计算天体在 Canvas 上的像素大小
  - 最多返回 200%（避免极端情况）

**`SkyMapCanvas.drawFovTargetOverlay()`**

- **视觉元素**：
  1. 虚线圆圈（setLineDash([5, 5])）
  2. 半透明填充（透明度 0.15）
  3. 文本标签（天体名称、大小、百分比）
  4. 匹配度提示（在 FOV 框下方）

- **颜色编码**：
  - 绿色 (`rgba(34, 197, 94, 0.6)`)：< 50%
  - 黄色 (`rgba(250, 204, 21, 0.6)`)：50-100%
  - 红色 (`rgba(239, 68, 68, 0.6)`)：> 100%

- **文本提示**：
  - `超出 FOV (X%)`：天体大于 FOV
  - `X% FOV`：正常显示占比

#### 数据依赖

**后端数据**：已确认包含
- `target.size`：单位：角分（arcmin）
- 通过 API 返回的推荐数据中已包含

**前端设备信息**：
```javascript
window.currentEquipment = {
  fov_horizontal: 10.3,  // 水平 FOV（度）
  fov_vertical: 6.9      // 垂直 FOV（度）
};
```

#### 集成点

**文件**: `frontend/src/scripts/main.js`

- 暴露 `window.currentEquipment` 供 Canvas 访问
- 设备切换时同步更新（`onPresetChange`）
- 调用 `skyMap.updateData({ equipment })`

**文件**: `frontend/src/scripts/utils/canvas.js`

- 添加 `state.fovTarget` 状态
- 在 `render()` 中调用 `drawFovTargetOverlay()`
- 实现 4 个核心方法

#### 视觉效果

```
天空图示例：
     ┌─────────────────────────────┐
     │                             │
     │     ┌─────────────┐         │
     │     │   FOV 框    │         │
     │     │             │         │
     │     │    ◉ M31    │ ← 基础圆点
     │     │    ╳        │ ← 真实大小轮廓
     │     │             │         │
     │     └─────────────┘         │
     │                             │
     └─────────────────────────────┘

文本标签：
  M31: 3.0°
  60% FOV

匹配度提示（FOV 框下方）：
  ⚠️ 天体过大，建议用更广角镜头  (红色)
  ✓ 大小适中                      (黄色)
  ✓ 大小合适                      (绿色)
  ℹ️ 天体较小，适合长焦拍摄        (灰色)
```

---

## 边界情况处理

### 功能 1：对焦+高亮

| 情况 | 处理方式 |
|------|----------|
| 目标低于地平线 | 仍然对焦，高度角设为 0° |
| 目标在方位角边界 (0°/360°) | 使用角度插值处理 |
| 用户正在拖动天空图 | 取消对焦动画，避免冲突 |
| 快速连续点击多个目标 | 取消前一个动画，启动新的 |

### 功能 2：FOV 叠加

| 情况 | 处理方式 |
|------|----------|
| FOV 框附近没有天体 | 不显示叠加层 |
| 天体大小为 0 或未定义 | 跳过该天体 |
| 设备信息未加载 | 使用默认 FOV (10° × 7°) |
| 天体超出 Canvas 边界 | 仍然绘制轮廓（部分可见） |
| 多个天体在阈值内 | 只显示最近的一个 |

---

## 性能考虑

### 功能 1：对焦+高亮

- **动画帧率**：60 FPS（使用 `requestAnimationFrame`）
- **动画时长**：600ms（约 36 帧）
- **开销**：每帧只需插值计算和重绘，开销极低
- **优化**：使用 `state.isAnimating` 标记避免重复启动

### 功能 2：FOV 叠加

- **检测频率**：每次重绘时执行（约 60 FPS）
- **优化策略**：
  - 只检测 FOV 框中心附近的天体（空间局部性）
  - 早期退出：FOV 框不可见时跳过
  - 距离计算使用平方值避免 `Math.sqrt`（除非需要精确距离）
- **缓存**：`state.fovTarget` 缓存检测结果，避免重复计算

---

## 测试计划

### 功能 1：对焦+高亮

#### 单元测试

- [ ] `focusOnTarget()`: 正确计算目标视角
- [ ] `animateFocus()`: 正确插值和边界处理
- [ ] `highlightTarget()`: 脉冲动画正确播放
- [ ] `lerpAngle()`: 正确处理 0°/360° 边界

#### 集成测试

- [ ] 点击推荐卡片 → 天空图对焦
- [ ] 对焦完成 → 高亮动画播放
- [ ] 快速点击多个卡片 → 正确取消旧动画

#### 手动测试

- [ ] 点击不同位置的天体（北/南/东/西）
- [ ] 点击低高度角的天体（< 10°）
- [ ] 连续快速点击 3 个以上天体
- [ ] 对焦过程中拖动天空图

### 功能 2：FOV 叠加

#### 单元测试

- [ ] `checkFovTargetOverlap()`: 正确检测重叠
- [ ] `getFovPixelSize()`: 正确转换角度到像素
- [ ] `calculateTargetFovRatio()`: 正确计算占比

#### 集成测试

- [ ] 拖动 FOV 框到 M31 → 显示大轮廓
- [ ] 拖动 FOV 框到小星云 → 显示小轮廓
- [ ] 切换设备预设 → 轮廓大小更新

#### 手动测试

- [ ] 测试不同大小的天体（3°, 30', 5'）
- [ ] 测试不同设备 FOV（广角、长焦）
- [ ] 测试边界情况（FOV 框在边缘）
- [ ] 测试多个天体靠近的情况

---

## 实现清单

### 功能 1：对焦+高亮

#### Canvas.js 修改

- [ ] 添加 `state.animationState` 和 `state.highlightedTarget`
- [ ] 实现 `focusOnTarget(target, options)`
- [ ] 实现 `animateFocus(timestamp)`
- [ ] 实现 `highlightTarget(targetId)`
- [ ] 实现 `easeInOutCubic(t)`
- [ ] 实现 `lerp(start, end, t)`
- [ ] 实现 `lerpAngle(start, end, t)`
- [ ] 修改 `drawTargets()` 添加高亮渲染

#### Main.js 修改

- [ ] 添加 `window.currentRecommendations`
- [ ] 修改推荐卡片点击事件处理器
- [ ] 添加错误处理（目标未找到）

### 功能 2：FOV 叠加

#### Canvas.js 修改

- [ ] 添加 `state.fovTarget`
- [ ] 实现 `checkFovTargetOverlap()`
- [ ] 实现 `getFovPixelSize()`
- [ ] 实现 `fovToPixels(fovDegrees)`
- [ ] 实现 `calculateTargetFovRatio(target)`
- [ ] 实现 `drawFovTargetOverlay()`
- [ ] 在 `render()` 中调用 `drawFovTargetOverlay()`

#### Main.js 修改

- [ ] 添加 `window.currentEquipment`
- [ ] 修改 `onPresetChange()` 同步设备信息
- [ ] 调用 `skyMap.updateData({ equipment })`

---

## 未来增强

### 短期（可选）

1. **对焦动画选项**：在设置中允许用户选择动画时长或关闭动画
2. **FOV 叠加开关**：允许用户隐藏叠加层（保持界面简洁）
3. **天体大小数据库**：为缺少 size 数据的天体提供估算值

### 长期（规划中）

1. **智能对焦**：根据天体类型自动调整高度角（星云 vs 星系）
2. **FOV 预览模式**：在推荐卡片中显示天体在当前 FOV 中的预览图
3. **多设备对比**：同时显示多个设备的 FOV 框，帮助选择最佳设备

---

## 参考资料

- [ easing-functions](https://easings.net/) - 缓动函数参考
- [ requestAnimationFrame MDN](https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame)
- Canvas API 文档：arc(), setLineDash(), createRadialGradient()

---

**设计完成日期**: 2025-02-17
**预计实现周期**: 2-3 天
**复杂度**: 中等
**优先级**: 高
