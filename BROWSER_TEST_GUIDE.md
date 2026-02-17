# 浏览器测试指南

**测试时间**: 2025-02-17
**应用地址**: http://localhost:3000
**API 文档**: http://localhost:8000/docs

---

## 🚀 快速开始

### 1. 打开应用

浏览器访问: **http://localhost:3000**

### 2. 打开开发者工具

- 按 **F12** 或右键 → 检查
- 切换到 **Console** 标签

---

## 🧪 第一步：自动验证（2分钟）

### 复制以下脚本到控制台：

```javascript
// ========== 自动验证脚本 ==========

console.log('='.repeat(50));
console.log('🔍 交互优化功能验证');
console.log('='.repeat(50));

// 1. 检查 skyMap 实例
if (!window.skyMap) {
  console.error('❌ skyMap 未找到！请确保页面完全加载');
} else {
  console.log('✅ skyMap 实例存在');

  // 2. 检查所有新方法
  const methods = [
    'easeInOutCubic',
    'lerp',
    'lerpAngle',
    'focusOnTarget',
    'animateFocus',
    'highlightTarget',
    'fovToPixels',
    'getFovPixelSize',
    'calculateTargetFovRatio',
    'checkFovTargetOverlap',
    'drawFovTargetOverlay'
  ];

  const missing = methods.filter(m => typeof window.skyMap[m] !== 'function');
  if (missing.length === 0) {
    console.log('✅ 所有11个新方法都存在');
    console.log('   ', methods.join(', '));
  } else {
    console.error('❌ 缺少方法:', missing);
  }

  // 3. 检查状态属性
  const state = window.skyMap.state;
  const stateChecks = [
    state.animationState ? 'animationState' : null,
    'highlightedTarget' in state ? 'highlightedTarget' : null,
    'highlightIntensity' in state ? 'highlightIntensity' : null,
    state.fovTarget ? 'fovTarget' : null
  ].filter(Boolean);

  if (stateChecks.length === 4) {
    console.log('✅ 所有状态属性都存在');
  } else {
    console.error('❌ 状态属性缺失:', stateChecks);
  }

  // 4. 检查设备信息
  if (window.currentEquipment) {
    console.log('✅ 设备信息已暴露:', window.currentEquipment);
  } else {
    console.error('❌ 设备信息未暴露');
  }
}

// 5. 计算功能测试
console.log('\n🧪 计算功能测试:');

const t = window.skyMap;
const eased = t.easeInOutCubic(0.5);
console.log('  easeInOutCubic(0.5):', eased.toFixed(3), '| 预期: 0.5',
  Math.abs(eased - 0.5) < 0.01 ? '✅' : '❌');

const angle = t.lerpAngle(350, 10, 0.5);
console.log('  lerpAngle(350, 10, 0.5):', angle.toFixed(0) + '°', '| 预期: 0°',
  angle >= 0 && angle <= 360 ? '✅' : '❌');

const testTarget = { size: 60, altitude: 45, azimuth: 180 };
const ratio = t.calculateTargetFovRatio(testTarget);
console.log('  FOV ratio:', ratio.overlapPercentage.toFixed(2), '| 预期: 0-2',
  ratio.overlapPercentage >= 0 && ratio.overlapPercentage <= 2 ? '✅' : '❌');

const fovSize = t.getFovPixelSize();
console.log('  FOV pixel size:', fovSize, '| 预期: {width, height}',
  fovSize.width && fovSize.height ? '✅' : '❌');

console.log('\n' + '='.repeat(50));
console.log('✅ 自动验证完成！');
console.log('='.repeat(50));
```

**预期输出**：
```
==================================================
🔍 交互优化功能验证
==================================================
✅ skyMap 实例存在
✅ 所有11个新方法都存在
✅ 所有状态属性都存在
✅ 设备信息已暴露: { fov_horizontal: 10.3, fov_vertical: 6.9 }

🧪 计算功能测试:
  easeInOutCubic(0.5): 0.500 | 预期: 0.5 ✅
  lerpAngle(350, 10, 0.5): 0° | 预期: 0° ✅
  FOV ratio: 0.41 | 预期: 0-2 ✅
  FOV pixel size: [object Object] | 预期: {width, height} ✅

==================================================
✅ 自动验证完成！
==================================================
```

---

## 🎯 第二步：手动功能测试（5分钟）

### 测试 1: 点击对焦+高亮

**步骤**：

1. **等待推荐加载**（页面加载后）
2. **在推荐面板找到第一个推荐卡片**
3. **点击该卡片**
4. **观察天空图**

**预期结果**：
- ✅ 天空图平滑旋转（约600毫秒）
- ✅ 目标移动到视野下方
- ✅ 目标显示脉冲高亮（1.5秒，3次跳动）
- ✅ 控制台显示 "Clicked target: XXX"

**如果失败**：
- 刷新页面重试
- 检查控制台是否有错误
- 确认推荐数据已加载

---

### 测试 2: 连续点击测试

**步骤**：

1. **点击第一个推荐卡片**
2. **立即点击第二个推荐卡片**（不要等动画完成）
3. **观察行为**

**预期结果**：
- ✅ 第一个动画立即取消
- ✅ 第二个动画开始
- ✅ 无冲突或卡顿
- ✅ 最终定位到第二个目标

---

### 测试 3: FOV 叠加功能

**步骤**：

1. **在天空图上找到 FOV 框**（白色圆圈，可拖动）
2. **将 FOV 框拖动到任意天体上**
3. **观察虚线圆圈和标签**

**预期结果**：
- ✅ 出现虚线圆圈（setLineDash虚线）
- ✅ 圆圈大小反映天体真实尺寸
- ✅ 颜色编码：
  - 🟢 绿色：天体 < 50% FOV
  - 🟡 黄色：天体 50-100% FOV
  - 🔴 红色：天体 > 100% FOV
- ✅ 显示两行文本：
  - "天体名称: X°"
  - "Y% FOV" 或 "超出 FOV (Y%)"

**如果看不到叠加**：
- 确保 FOV 框中心非常接近天体
- 尝试拖到更大的天体上
- 检查控制台是否有错误

---

### 测试 4: 设备切换测试

**步骤**：

1. **拖动 FOV 框到某个天体上**（记住圆圈大小）
2. **在右侧面板切换设备预设**
3. **观察圆圈大小变化**

**预期结果**：
- ✅ 圆圈大小根据新设备 FOV 变化
- ✅ 百分比数字更新
- ✅ 颜色编码可能改变
- ✅ 文本标签更新

---

## 🔍 第三步：高级测试（可选）

### 测试 5: 手动触发动画

**在控制台执行**：

```javascript
// 手动触发对焦（不点击卡片）
window.skyMap.focusOnTarget(
  {
    azimuth: 90,    // 正东方向
    altitude: 60,   // 60度高度
    id: 'manual-test',
    name: 'Manual Test'
  },
  {
    duration: 600,  // 600ms 动画
    elevation: 15,  // 目标在视野下方15度
    onComplete: () => console.log('✅ 对焦完成！')
  }
);

// 立即触发高亮
window.skyMap.highlightTarget('manual-test');
```

**预期结果**：
- 天空图旋转到正东方向（90°）
- 然后显示脉冲高亮

---

### 测试 6: 性能测试

**在控制台执行**：

```javascript
// FPS 测试
let frames = 0;
let startTime = performance.now();

function countFrames() {
  frames++;
  const elapsed = performance.now() - startTime;
  if (elapsed < 1000) {
    requestAnimationFrame(countFrames);
  } else {
    console.log('📊 FPS: ' + frames + ' (预期: ~60)');
    console.log(frames >= 55 ? '✅ 性能良好' : '⚠️ 性能需要优化');
  }
}
countFrames();

// FOV 检测性能测试
const iterations = 100;
const start = performance.now();

for (let i = 0; i < iterations; i++) {
  window.skyMap.checkFovTargetOverlap();
}

const elapsed = performance.now() - start;
const avg = elapsed / iterations;

console.log('📊 FOV 检测性能:');
console.log('  总耗时: ' + elapsed.toFixed(2) + 'ms');
console.log('  平均每次: ' + avg.toFixed(3) + 'ms');
console.log(avg < 1 ? '✅ 性能优秀' : '⚠️ 需要优化');
```

**预期结果**：
- FPS >= 55
- FOV 检测平均 < 1ms

---

## 📸 验证截图清单

请测试以下场景并截图：

### 场景 1：对焦动画
- [ ] 推荐卡片加载完成
- [ ] 点击卡片，天空图开始旋转
- [ ] 目标显示高亮效果
- [ ] 截图：包含推荐面板和天空图

### 场景 2：FOV 叠加 - 小天体
- [ ] 拖动 FOV 框到小天体上
- [ ] 显示绿色虚线圆圈
- [ ] 显示 "< 50% FOV"
- [ ] 截图：FOV 框和绿色圆圈

### 场景 3：FOV 叠加 - 大天体
- [ ] 拖动 FOV 框到大天体上
- [ ] 显示红色虚线圆圈
- [ ] 显示 "超出 FOV"
- [ ] 截图：FOV 框和红色圆圈

### 场景 4：设备切换
- [ ] 切换设备预设
- [ ] 圆圈大小明显变化
- [ ] 截图：切换前后的对比

---

## 🐛 问题排查

### 问题：控制台有错误

**可能原因**：
- 推荐数据未加载
- Canvas 未初始化
- 语法错误

**解决方法**：
1. 刷新页面（F5）
2. 清除缓存并刷新
3. 检查服务器是否启动

---

### 问题：点击卡片没反应

**检查步骤**：
1. 在控制台输入：
```javascript
document.querySelectorAll('.target-card').length
```
2. 应该显示推荐卡片数量（如20）
3. 检查 skyMap 是否存在：
```javascript
window.skyMap
```

---

### 问题：FOV 叠加不显示

**检查步骤**：
1. 在控制台输入：
```javascript
window.skyMap.state.targets.length
```
2. 应该显示天体数量
3. 检查设备信息：
```javascript
window.currentEquipment
```
4. 手动调用检测：
```javascript
window.skyMap.checkFovTargetOverlap()
```

---

## ✅ 测试完成标准

### 必须通过的测试：

- [ ] 所有11个新方法存在
- [ ] 点击推荐卡片触发对焦动画
- [ ] 对焦完成后显示脉冲高亮
- [ ] 拖动 FOV 框到天体显示虚线圆圈
- [ ] 圆圈颜色编码正确（绿/黄/红）
- [ ] 显示文本标签
- [ ] 切换设备时圆圈大小更新
- [ ] 无控制台错误
- [ ] 动画流畅（无明显卡顿）

---

## 📝 测试报告模板

**测试人员**: _____
**测试时间**: _____
**浏览器**: _____
**操作系统**: _____

### 功能测试结果：

| 功能 | 状态 | 备注 |
|------|------|------|
| 点击对焦 | ☐ 通过 / ☐ 失败 | 动画时长: ___ ms |
| 脉冲高亮 | ☐ 通过 / ☐ 失败 | 脉冲次数: 3 |
| FOV 叠加 | ☐ 通过 / ☐ 失败 | 颜色正确: ☐ / ☐ |
| 设备切换 | ☐ 通过 / ☐ 失败 | 更新正确: ☐ / ☐ |

### 性能测试结果：

| 指标 | 结果 | 实际值 |
|------|------|--------|
| FPS | ☐ / ☐ | ___ |
| 对焦时长 | ☐ / ☐ | ___ ms |
| FOV 检测 | ☐ / ☐ | ___ ms |

### 发现的问题：

1.
2.
3.

---

**测试完成后，请将结果反馈！** 🚀
