# Interactive Optimization Implementation Plan

**Date**: 2025-02-17
**Status**: Ready for Implementation
**Branch**: `interactive`

---

## Phase 0: Documentation Discovery (COMPLETED)

### Allowed APIs & Patterns

**Core Projection Method**:
- File: `frontend/src/scripts/utils/canvas.js:200-252`
- Signature: `projectFromCenter(azimuth, altitude)` → `{ x, y, z, visible, scale }`
- Parameters: azimuth (0-360°), altitude (0-90°)
- Returns: visible=false for points behind viewer or below horizon

**State Update Pattern**:
- File: `frontend/src/scripts/utils/canvas.js:596-599`
- Method: `updateData(data)` - Uses spread operator for immutable update
- Pattern: `this.state = { ...this.state, ...data }; this.render();`

**Render Cycle**:
- File: `frontend/src/scripts/utils/canvas.js:254-268`
- Order: background → celestial sphere → grid → horizon → zones → FOV frame → heatmap → moon → targets → compass
- Pattern: All draw methods use `this.state` and `this.ctx`

**Target Drawing Pattern**:
- File: `frontend/src/scripts/utils/canvas.js:430-511`
- Steps: Sort by z-axis → Filter visible → Scale size → Draw with hover effects
- Base size: 8px, scaled by `pos.scale * 0.15`, clamped to [3, 20]

**Event Handling**:
- File: `frontend/src/scripts/utils/canvas.js:72-191`
- Pattern: `getBoundingClientRect()` for coordinates → track drag state → update state → render()
- Callbacks: Optional chaining `this.onEventName?.(data)`

**Hit Detection**:
- File: `frontend/src/scripts/utils/canvas.js:538-576`
- Method: Distance-based circular detection
- Formula: `Math.sqrt((mouseX - x)² + (mouseY - y)²) < size + 5`

### Anti-Patterns to Avoid

**DO NOT**:
- ❌ Use deprecated or non-existent animation APIs (none exist in codebase)
- ❌ Modify state without calling `render()`
- ❌ Skip the `pos.visible` check when drawing
- ❌ Use hardcoded colors/sizes (should be configurable)
- ❌ Forget to normalize angles (0-360°) when interpolating azimuth
- ❌ Access `this.state.targets` without checking if array exists

**MUST**:
- ✅ Use spread operator for state updates
- ✅ Call `this.render()` after state mutations
- ✅ Filter objects using `pos.visible && altitude > 0`
- ✅ Use `requestAnimationFrame` for animations (not currently in codebase)
- ✅ Follow the render order: background → objects → overlay → compass

---

## Phase 1: Animation System Foundation

**Goal**: Implement smooth animation infrastructure for canvas transitions

### Tasks

**Task 1.1: Add Animation State**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After line 54 (in constructor, after `this.state`)
- Copy pattern from: Lines 30-54 (existing state structure)

```javascript
// Add to this.state in constructor:
animationState: {
  isAnimating: false,
  startTime: null,
  startView: null,    // { azimuth, altitude }
  endView: null,      // { azimuth, altitude }
  duration: 600,      // ms
  onComplete: null    // callback
},
highlightedTarget: null,    // target ID
highlightIntensity: 0        // 0-1, pulse intensity
```

**Verification**:
- [ ] State properties exist in canvas instance
- [ ] No render errors on page load
- [ ] Can access `skyMap.state.animationState` from console

**Task 1.2: Implement Easing Functions**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After line 269 (after `projectFromCenter` method)

```javascript
// ========== Animation Utilities ==========

/**
 * Ease-in-out cubic easing function
 * @param {number} t - Progress (0-1)
 * @returns {number} Eased value
 */
easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/**
 * Linear interpolation
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} t - Progress (0-1)
 * @returns {number} Interpolated value
 */
lerp(start, end, t) {
  return start + (end - start) * t;
}

/**
 * Angular interpolation (handles 0°/360° boundary)
 * @param {number} start - Start angle (degrees)
 * @param {number} end - End angle (degrees)
 * @param {number} t - Progress (0-1)
 * @returns {number} Interpolated angle
 */
lerpAngle(start, end, t) {
  const diff = end - start;
  const normalizedDiff = ((diff + 180) % 360) - 180;
  return start + normalizedDiff * t;
}
```

**Verification**:
- [ ] `easeInOutCubic(0.5)` returns approximately 0.5
- [ ] `lerpAngle(350, 10, 0.5)` handles boundary correctly (≈ 0°)
- [ ] Functions are pure (no side effects)

**Task 1.3: Test Animation Loop**
- Create manual test in browser console:
```javascript
const skyMap = window.skyMap;
const result = skyMap.easeInOutCubic(0.5);
console.log('Easing test:', result); // Should be ~0.5
```

**Anti-Pattern Guards**:
- ❌ Don't use CSS transitions (not applicable to canvas)
- ❌ Don't modify easing function signatures
- ❌ Don't forget to normalize angles in `lerpAngle`

---

## Phase 2: Focus-On-Target Feature

**Goal**: Click recommendation card → sky map smoothly rotates to target

### Tasks

**Task 2.1: Implement focusOnTarget() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After easing functions (Task 1.2)
- Reference: Mouse drag handling pattern from lines 139-154

```javascript
/**
 * Smoothly animate view to focus on target
 * @param {Object} target - { azimuth, altitude, id, name }
 * @param {Object} options - { duration, elevation, onComplete }
 */
focusOnTarget(target, options = {}) {
  const {
    duration = 600,
    elevation = 15,  // Target will be 15° below center
    onComplete = null
  } = options;

  // Calculate target view position
  const targetAzimuth = target.azimuth;
  const targetAltitude = Math.max(0, target.altitude - elevation);

  // Cancel existing animation
  if (this.state.animationState.isAnimating) {
    this.state.animationState.isAnimating = false;
  }

  // Setup animation state
  this.state.animationState = {
    isAnimating: true,
    startTime: null,
    startView: {
      azimuth: this.view.azimuth,
      altitude: this.view.altitude
    },
    endView: {
      azimuth: targetAzimuth,
      altitude: targetAltitude,
      zoom: this.view.zoom
    },
    duration,
    onComplete
  };

  // Start animation loop
  requestAnimationFrame((timestamp) => this.animateFocus(timestamp));
}
```

**Verification**:
- [ ] Method exists on skyMap instance
- [ ] Calling with test target doesn't throw error
- [ ] Animation state is set correctly

**Task 2.2: Implement animateFocus() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `focusOnTarget()` method
- Reference: Render cycle pattern from line 599

```javascript
/**
 * Animation loop for focus transition
 * @param {number} timestamp - Current timestamp from requestAnimationFrame
 */
animateFocus(timestamp) {
  if (!this.state.animationState.startTime) {
    this.state.animationState.startTime = timestamp;
  }

  const elapsed = timestamp - this.state.animationState.startTime;
  const progress = Math.min(elapsed / this.state.animationState.duration, 1);

  // Apply easing
  const eased = this.easeInOutCubic(progress);

  // Interpolate view angles
  this.view.azimuth = this.lerpAngle(
    this.state.animationState.startView.azimuth,
    this.state.animationState.endView.azimuth,
    eased
  );
  this.view.altitude = this.lerp(
    this.state.animationState.startView.altitude,
    this.state.animationState.endView.altitude,
    eased
  );

  this.render();

  // Continue or finish animation
  if (progress < 1) {
    requestAnimationFrame((t) => this.animateFocus(t));
  } else {
    this.state.animationState.isAnimating = false;
    if (this.state.animationState.onComplete) {
      this.state.animationState.onComplete();
    }
  }
}
```

**Verification**:
- [ ] Animation completes in ~600ms
- [ ] View angles reach target values
- [ ] `onComplete` callback is called
- [ ] Animation can be cancelled by starting new one

**Task 2.3: Connect to Recommendation Cards**
- File: `frontend/src/scripts/main.js`
- Location: Line 31 (add variable) and lines 729-760 (modify click handler)
- Reference: Existing click handler pattern

**Step 1**: Add storage variable after line 30:
```javascript
let currentRecommendations = []; // Store for click handlers
```

**Step 2**: Modify `loadRecommendations()` after line 636:
```javascript
const recommendations = data.recommendations || [];
currentRecommendations = recommendations; // Store for click access
```

**Step 3**: Replace click handler (lines 729-736):
```javascript
document.querySelectorAll('.target-card').forEach(card => {
  card.addEventListener('click', () => {
    const targetId = card.dataset.targetId;
    console.log('Clicked target:', targetId);

    // Find target in recommendations
    const target = currentRecommendations.find(rec => rec.target.id === targetId);
    if (!target) {
      console.error('Target not found:', targetId);
      return;
    }

    // Focus on target
    skyMap.focusOnTarget(
      {
        id: target.target.id,
        name: target.target.name,
        azimuth: target.current_position.azimuth,
        altitude: target.current_position.altitude
      },
      {
        duration: 600,
        elevation: 15,
        onComplete: () => {
          skyMap.highlightTarget(targetId);
        }
      }
    );
  });
});
```

**Verification**:
- [ ] Click card → sky map animates to target
- [ ] Target ends up in lower portion of view
- [ ] Animation is smooth (600ms)
- [ ] Can click multiple cards in succession
- [ ] Console shows no errors

**Anti-Pattern Guards**:
- ❌ Don't assume `currentRecommendations` exists (check if undefined)
- ❌ Don't forget to normalize angles
- ❌ Don't modify target objects from API response
- ❌ Don't set duration below 300ms (too jarring)

---

## Phase 3: Highlight Animation Feature

**Goal**: After focus completes, show pulsing highlight on target

### Tasks

**Task 3.1: Implement highlightTarget() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `animateFocus()` method
- Reference: Moon hover pattern from lines 889-931

```javascript
/**
 * Show pulsing highlight animation on target
 * @param {string} targetId - Target identifier
 */
highlightTarget(targetId) {
  this.state.highlightedTarget = targetId;

  const duration = 1500; // 1.5 seconds
  const pulses = 3;      // 3 pulses
  const startTime = performance.now();

  const animate = (timestamp) => {
    const elapsed = timestamp - startTime;
    const progress = elapsed / duration;

    if (progress < 1) {
      // Calculate which pulse (0, 1, 2)
      const pulseProgress = (progress * pulses) % 1;

      // Sine wave pulse: 0 → 1 → 0
      const intensity = Math.sin(pulseProgress * Math.PI);

      this.state.highlightIntensity = intensity;
      this.render();
      requestAnimationFrame(animate);
    } else {
      // Animation complete
      this.state.highlightedTarget = null;
      this.state.highlightIntensity = 0;
      this.render();
    }
  };

  requestAnimationFrame(animate);
}
```

**Verification**:
- [ ] Animation lasts ~1.5 seconds
- [ ] Shows 3 distinct pulses
- [ ] State clears after completion
- [ ] Multiple calls cancel previous animation

**Task 3.2: Modify drawTargets() for Highlight**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: Lines 650-653 (after border stroke, before text)
- Reference: Hover glow pattern from lines 463-474

```javascript
// Draw border
ctx.strokeStyle = isHovered ? '#FFFFFF' : color;
ctx.lineWidth = isHovered ? 2 : 1;
ctx.stroke();

// Draw highlight animation (NEW)
if (this.state.highlightedTarget === target.id && this.state.highlightIntensity > 0) {
  const highlightSize = size * (1 + this.state.highlightIntensity * 0.8);
  const alpha = 0.3 + this.state.highlightIntensity * 0.4;

  ctx.save();

  // Outer pulse ring
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, highlightSize, 0, Math.PI * 2);
  ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
  ctx.lineWidth = 3;
  ctx.stroke();

  // Inner highlight glow
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, highlightSize * 0.6, 0, Math.PI * 2);
  ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.5})`;
  ctx.fill();

  ctx.restore();
}

// Draw name
```

**Verification**:
- [ ] Highlight appears after focus completes
- [ ] Pulse size scales correctly (1.0x to 1.8x)
- [ ] Opacity fades in/out smoothly
- [ ] Highlight doesn't interfere with hover effects
- [ ] Multiple targets don't all highlight (only selected one)

**Task 3.3: Test Complete Flow**
- Manual test sequence:
  1. Load recommendations
  2. Click first card
  3. Verify: sky map rotates (600ms)
  4. Verify: target highlights (1.5s, 3 pulses)
  5. Click second card during animation
  6. Verify: first animation cancels, second starts

**Verification Commands**:
```javascript
// From browser console
const recs = window.currentRecommendations;
const firstTarget = {
  id: recs[0].target.id,
  azimuth: recs[0].current_position.azimuth,
  altitude: recs[0].current_position.altitude
};
window.skyMap.focusOnTarget(firstTarget, {
  duration: 600,
  elevation: 15,
  onComplete: () => console.log('Focus complete!')
});
```

**Anti-Pattern Guards**:
- ❌ Don't check `highlightedTarget` without checking `highlightIntensity`
- ❌ Don't use `rgba()` without validating alpha (0-1)
- ❌ Don't forget `ctx.save()`/`restore()` for state isolation
- ❌ Don't make pulse duration too long (> 2s)

---

## Phase 4: FOV Overlay State

**Goal**: Prepare state for FOV target size overlay feature

### Tasks

**Task 4.1: Add FOV Target State**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `highlightIntensity` (line 67)
- Reference: Existing `fovFrame` state pattern (lines 39-44)

```javascript
// Add to this.state in constructor:
fovTarget: {
  target: null,        // Target object
  overlapPercentage: 0, // 0-1, target size relative to FOV
  canvasSize: 0        // Pixel diameter on canvas
}
```

**Verification**:
- [ ] State property exists
- [ ] Can access `skyMap.state.fovTarget.target`
- [ ] Initial values are correct (null, 0, 0)

**Task 4.2: Expose Equipment to Window**
- File: `frontend/src/scripts/main.js`
- Location: After line 25 (after `currentEquipment` declaration)
- Reference: Existing global variable pattern

```javascript
// Expose for Canvas access
window.currentEquipment = currentEquipment;
```

**Verification**:
- [ ] `window.currentEquipment` exists
- [ ] Has `fov_horizontal` and `fov_vertical` properties
- [ ] Values match initial equipment (10.3°, 6.9°)

**Task 4.3: Sync Equipment on Changes**
- File: `frontend/src/scripts/main.js`
- Locations:
  - Line 467: After initial equipment load
  - Line 503: In custom mode reset
  - Line 518: After preset change
  - Line 579: After custom calculation

**Pattern to add at each location**:
```javascript
window.currentEquipment = currentEquipment;
```

**Verification**:
- [ ] Change equipment preset → `window.currentEquipment` updates
- [ ] Custom calculation → `window.currentEquipment` updates
- [ ] Switch to custom mode → `window.currentEquipment` updates

**Anti-Pattern Guards**:
- ❌ Don't assume `window.currentEquipment` exists in canvas (check first)
- ❌ Don't sync before `currentEquipment` is updated
- ❌ Don't forget all 4 sync locations

---

## Phase 5: FOV Detection System

**Goal**: Detect when FOV frame is near a target

### Tasks

**Task 5.1: Implement fovToPixels() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `highlightTarget()` method
- Reference: Projection pattern from lines 235-240

```javascript
/**
 * Convert FOV angle to canvas pixels
 * @param {number} fovDegrees - FOV angle in degrees
 * @returns {number} Size in pixels
 */
fovToPixels(fovDegrees) {
  const { fov } = this.config; // View FOV (90°)
  const { radius } = this.config;

  // Linear mapping: 90° → radius * 2
  return (fovDegrees / fov) * radius * 2;
}
```

**Verification**:
- [ ] `fovToPixels(90)` returns approximately `radius * 2`
- [ ] `fovToPixels(45)` returns approximately `radius`
- [ ] Returns reasonable values (not NaN or Infinity)

**Task 5.2: Implement getFovPixelSize() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `fovToPixels()`

```javascript
/**
 * Get current FOV frame size in pixels
 * @returns {Object} - { width, height }
 */
getFovPixelSize() {
  const equipment = window.currentEquipment;

  if (!equipment || !equipment.fov_horizontal) {
    // Default FOV: 10° × 7°
    return {
      width: this.fovToPixels(10),
      height: this.fovToPixels(7)
    };
  }

  return {
    width: this.fovToPixels(equipment.fov_horizontal),
    height: this.fovToPixels(equipment.fov_vertical)
  };
}
```

**Verification**:
- [ ] Returns object with `width` and `height`
- [ ] Default values are reasonable
- [ ] Uses current equipment when available
- [ ] Values change when equipment changes

**Task 5.3: Implement calculateTargetFovRatio() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `getFovPixelSize()`
- Reference: Target data structure from line 636 (`target.size` in arcmin)

```javascript
/**
 * Calculate target size relative to FOV
 * @param {Object} target - Target object with `size` property (arcmin)
 * @returns {Object} - { overlapPercentage, canvasSize }
 */
calculateTargetFovRatio(target) {
  const equipment = window.currentEquipment;

  // Convert target size from arcmin to degrees
  const targetSizeDegrees = target.size / 60;

  // Calculate FOV diagonal
  const fovH = equipment?.fov_horizontal || 10;
  const fovV = equipment?.fov_vertical || 7;
  const fovDiagonal = Math.sqrt(fovH * fovH + fovV * fovV);

  // Ratio (max 2.0 = 200%)
  const overlapPercentage = Math.min(targetSizeDegrees / fovDiagonal, 2);

  // Canvas pixel size
  const canvasSize = this.fovToPixels(targetSizeDegrees);

  return {
    overlapPercentage,
    canvasSize
  };
}
```

**Verification**:
- [ ] Handles targets with `size` in arcmin
- [ ] Returns `overlapPercentage` between 0 and 2
- [ ] Returns `canvasSize` in pixels
- [ ] Works with default equipment (10° × 7°)

**Task 5.4: Implement checkFovTargetOverlap() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `calculateTargetFovRatio()`
- Reference: Hit detection pattern from lines 552-576

```javascript
/**
 * Check if FOV frame overlaps with any target
 * @returns {Object|null} - { target, overlapPercentage, canvasSize, distance }
 */
checkFovTargetOverlap() {
  const { fovFrame } = this.state;
  const { targets } = this.state;

  if (!targets || targets.length === 0) return null;

  // Get FOV center position
  const fovCenter = this.projectFromCenter(
    fovFrame.center.azimuth,
    fovFrame.center.altitude
  );

  if (!fovCenter.visible) return null;

  // Threshold: 50% of smaller FOV dimension
  const fovPixelSize = this.getFovPixelSize();
  const thresholdDistance = Math.min(fovPixelSize.width, fovPixelSize.height) * 0.5;

  // Find closest target
  let closestTarget = null;
  let minDistance = Infinity;

  targets.forEach(target => {
    if (target.altitude <= 0) return;

    const targetPos = this.projectFromCenter(target.azimuth, target.altitude);
    if (!targetPos.visible) return;

    // Calculate distance
    const dx = targetPos.x - fovCenter.x;
    const dy = targetPos.y - fovCenter.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance < minDistance && distance < thresholdDistance) {
      minDistance = distance;
      closestTarget = target;
    }
  });

  if (!closestTarget) return null;

  // Calculate overlap
  const { overlapPercentage, canvasSize } = this.calculateTargetFovRatio(closestTarget);

  return {
    target: closestTarget,
    overlapPercentage,
    canvasSize,
    distance: minDistance
  };
}
```

**Verification**:
- [ ] Returns null when no targets nearby
- [ ] Returns closest target when multiple nearby
- [ ] Only considers targets above horizon
- [ ] Threshold distance is reasonable (not too large/small)

**Task 5.5: Test Detection**
- Manual test in browser:
```javascript
// Drag FOV frame to a target
// Check console:
const overlap = window.skyMap.checkFovTargetOverlap();
console.log('Overlap:', overlap);
// Should show target info when near, null when far
```

**Anti-Pattern Guards**:
- ❌ Don't assume `targets` array exists
- ❌ Don't forget `pos.visible` check
- ❌ Don't use Euclidean distance without squaring (can skip sqrt for comparison)
- ❌ Don't set threshold too large (will match too many targets)

---

## Phase 6: FOV Overlay Rendering

**Goal**: Draw target size overlay when FOV is near target

### Tasks

**Task 6.1: Implement drawFovTargetOverlay() Method**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: After `checkFovTargetOverlap()`
- Reference: Moon drawing pattern from lines 894-947

```javascript
/**
 * Draw target size overlay when FOV overlaps target
 */
drawFovTargetOverlay() {
  const overlap = this.checkFovTargetOverlap();

  if (!overlap) {
    this.state.fovTarget.target = null;
    return;
  }

  // Update state
  this.state.fovTarget = overlap;

  const { target, overlapPercentage, canvasSize } = overlap;
  const { ctx } = this;

  // Get target position
  const pos = this.projectFromCenter(target.azimuth, target.altitude);
  if (!pos.visible) return;

  const radius = canvasSize / 2;

  ctx.save();

  // Draw dashed circle for target size
  ctx.beginPath();
  ctx.setLineDash([5, 5]); // Dashed line
  ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);

  // Color by overlap percentage
  let color;
  if (overlapPercentage > 1) {
    color = 'rgba(239, 68, 68, 0.6)';  // Red: too large
  } else if (overlapPercentage > 0.5) {
    color = 'rgba(250, 204, 21, 0.6)'; // Yellow: large
  } else {
    color = 'rgba(34, 197, 94, 0.6)';  // Green: good fit
  }

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Semi-transparent fill
  ctx.fillStyle = color.replace('0.6', '0.15');
  ctx.fill();

  // Draw labels
  ctx.setLineDash([]); // Reset to solid
  ctx.fillStyle = '#FFFFFF';
  ctx.font = 'bold 12px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';

  const sizeDegrees = (target.size / 60).toFixed(1);
  const percentage = Math.round(overlapPercentage * 100);

  // Target name and size
  ctx.fillText(`${target.name}: ${sizeDegrees}°`, pos.x, pos.y - radius - 8);

  // Percentage
  ctx.font = '11px sans-serif';
  ctx.fillStyle = color.replace('0.6', '1.0');
  ctx.fillText(
    overlapPercentage > 1
      ? `超出 FOV (${percentage}%)`
      : `${percentage}% FOV`,
    pos.x,
    pos.y - radius - 24
  );

  ctx.restore();
}
```

**Verification**:
- [ ] Overlay appears when FOV is near target
- [ ] Circle size matches target size in FOV
- [ ] Color coding is correct (green/yellow/red)
- [ ] Labels are readable and positioned correctly
- [ ] Overlay disappears when FOV moves away

**Task 6.2: Add to Render Cycle**
- File: `frontend/src/scripts/utils/canvas.js`
- Location: Line 283 (after `drawFOVFrame()`)
- Reference: Render cycle order from lines 277-285

```javascript
render() {
  const { ctx, config } = this;

  ctx.clearRect(0, 0, config.width, config.height);

  this.drawBackground();
  this.drawCelestialSphere();
  this.drawGrid();
  this.drawHorizon();
  this.drawVisibleZones();
  this.drawFOVFrame();
  this.drawFovTargetOverlay(); // NEW - after FOV frame, before heatmap
  this.drawMoonlightPollutionHeatmap();
  this.drawMoon();
  this.drawTargets();
  this.drawCompass();
}
```

**Verification**:
- [ ] Overlay renders in correct order (above FOV frame)
- [ ] Overlay doesn't interfere with other elements
- [ ] Render cycle completes without errors
- [ ] Frame rate remains smooth (60 FPS)

**Task 6.3: Test Complete FOV Feature**
- Manual test sequence:
  1. Select different equipment preset
  2. Drag FOV frame to large target (e.g., M31)
  3. Verify: Red overlay shows, label says "超出 FOV"
  4. Drag FOV to small target
  5. Verify: Green overlay shows, label says "X% FOV"
  6. Change equipment preset
  7. Verify: Overlay size updates

**Verification Commands**:
```javascript
// Check equipment
console.log('Equipment:', window.currentEquipment);

// Check overlap
const overlap = window.skyMap.checkFovTargetOverlap();
console.log('Overlap:', overlap);

// Test calculation
const testTarget = { size: 180 }; // M31 in arcmin
const ratio = window.skyMap.calculateTargetFovRatio(testTarget);
console.log('Ratio:', ratio);
```

**Anti-Pattern Guards**:
- ❌ Don't draw overlay when `overlap` is null
- ❌ Don't forget to reset `setLineDash([])` after dashed lines
- ❌ Don't use string replacement for alpha without checking format
- ❌ Don't draw text without checking `pos.visible`

---

## Phase 7: Final Verification

**Goal**: Comprehensive testing and validation

### Tasks

**Task 7.1: Automated Checks**

Run in browser console:

```javascript
// 1. Check all methods exist
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
console.log('Missing methods:', missing); // Should be []

// 2. Check state structure
const state = window.skyMap.state;
console.log('Has animationState:', !!state.animationState);
console.log('Has highlightedTarget:', 'highlightedTarget' in state);
console.log('Has fovTarget:', 'fovTarget' in state);

// 3. Check equipment exposure
console.log('Equipment exposed:', !!window.currentEquipment);
console.log('Equipment has FOV:', 'fov_horizontal' in window.currentEquipment);

// 4. Test calculations
const testTarget = { size: 60, altitude: 45, azimuth: 180 };
const ratio = window.skyMap.calculateTargetFovRatio(testTarget);
console.log('Calculation test:', ratio);
console.log('Ratio valid:', ratio.overlapPercentage >= 0 && ratio.overlapPercentage <= 2);
```

**Task 7.2: Interactive Tests**

**Test 1: Focus Animation**
1. Load application
2. Click first recommendation card
3. **Expected**: Sky map smoothly rotates (600ms)
4. **Expected**: Target pulses (1.5s, 3 times)
5. **Fail**: If animation is jerky or doesn't complete

**Test 2: Multi-Click**
1. Click card 1
2. Immediately click card 2
3. **Expected**: First animation cancels, second starts
4. **Fail**: If animations queue or overlap

**Test 3: FOV Overlay**
1. Drag FOV frame to a target
2. **Expected**: Dashed circle appears
3. **Expected**: Color matches size (green/yellow/red)
4. **Expected**: Labels show name and percentage
5. **Fail**: If overlay is wrong size or color

**Test 4: Equipment Change**
1. Change equipment preset
2. Drag FOV to same target
3. **Expected**: Overlay size changes
4. **Fail**: If overlay stays same size

**Test 5: Edge Cases**
1. Click card with target below horizon
2. **Expected**: Still focuses, altitude clamped to 0
3. Drag FOV to edge of sky
4. **Expected**: No crashes, graceful handling
5. **Fail**: If errors in console

**Task 7.3: Performance Checks**

```javascript
// Check frame rate
let frames = 0;
let startTime = performance.now();

function countFrames() {
  frames++;
  const elapsed = performance.now() - startTime;
  if (elapsed < 1000) {
    requestAnimationFrame(countFrames);
  } else {
    console.log('FPS:', frames);
    console.log('Should be ~60 FPS');
  }
}
countFrames();

// Check animation smoothness
const start = performance.now();
window.skyMap.focusOnTarget(
  { azimuth: 90, altitude: 45, id: 'test' },
  { duration: 600, onComplete: () => {
    const elapsed = performance.now() - start;
    console.log('Animation took:', elapsed, 'ms');
    console.log('Should be ~600ms');
  }}
);
```

**Task 7.4: Code Quality Checks**

```bash
# From project root
cd frontend

# Check for syntax errors
npm run lint 2>&1 | grep -i error

# Check for console.log left in production
grep -n "console\.log" src/scripts/utils/canvas.js | grep -v "//"

# Check for TODO comments
grep -n "TODO" src/scripts/utils/canvas.js

# Check for hardcoded values (should be configurable)
grep -n "const.*=.*[0-9]" src/scripts/utils/canvas.js | grep -E "(color|size|duration)" | head -10
```

**Task 7.5: Anti-Pattern Verification**

Search for and verify these patterns are NOT present:

```bash
# Don't use CSS transitions
grep -r "transition\|animate" frontend/src/scripts/utils/canvas.js | grep -v "//"

# Don't modify state without rendering
grep -A2 "this\.state\." frontend/src/scripts/utils/canvas.js | grep -v "render()"

# Don't skip visible check
grep -B5 -A5 "forEach.*target" frontend/src/scripts/utils/canvas.js | grep "visible"

# Don't assume angles are normalized
grep -n "% 360" frontend/src/scripts/utils/canvas.js

# Don't use deprecated methods
grep -r "save\()\|restore()" frontend/src/scripts/utils/canvas.js | grep -v "ctx\."
```

**Task 7.6: Browser Compatibility**

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)

Check for:
- `requestAnimationFrame` support
- Canvas rendering performance
- `Math.pow`, `Math.sin`, `Math.sqrt` accuracy

**Task 7.7: Documentation Updates**

Update design document with actual implementation:
1. Note any deviations from design
2. Document performance measurements
3. List known limitations
4. Record code locations for future maintenance

---

## Phase 8: Clean-Up and Polish

**Goal**: Production-ready code

### Tasks

**Task 8.1: Remove Debug Code**

```bash
# Search and remove temporary console.logs
grep -n "console\.log.*test\|debug\|TEST" frontend/src/scripts/utils/canvas.js

# Keep only intentional console.logs for errors
```

**Task 8.2: Add JSDoc Comments**

Ensure all new methods have:
- Description
- `@param` tags with types
- `@returns` tags
- Usage examples where helpful

**Task 8.3: Code Formatting**

```bash
cd frontend
npm run format
npm run lint -- --fix
```

**Task 8.4: Final Code Review Checklist**

- [ ] No hardcoded values that should be configurable
- [ ] All state mutations followed by `render()`
- [ ] All angle interpolations use `lerpAngle()`
- [ ] All canvas operations use `save()`/`restore()`
- [ ] No memory leaks (event listeners cleaned up)
- [ ] Error handling for edge cases
- [ ] Consistent code style with existing codebase

**Task 8.5: Create Git Commit**

```bash
git add frontend/src/scripts/utils/canvas.js frontend/src/scripts/main.js
git commit -m "feat: implement interactive optimization (focus + FOV overlay)

- Smooth focus animation (600ms, easeInOutCubic)
- Pulse highlight effect (1.5s, 3 pulses)
- FOV target size overlay with color coding
- Equipment-aware size calculations
- Click-to-focus on recommendation cards

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary

**Total Phases**: 8
**Estimated Time**: 3-4 hours
**Lines of Code**: ~450
**Files Modified**: 2
**New Methods**: 11

**Key Dependencies**:
- `requestAnimationFrame` (browser API)
- Canvas 2D Context (existing)
- Existing projection method `projectFromCenter()`
- Equipment data from `window.currentEquipment`

**Risks and Mitigations**:
1. **Performance**: Animation loops could impact frame rate
   - Mitigation: Early exit checks, efficient calculations
2. **Edge Cases**: Targets at horizon, angle boundaries
   - Mitigation: Clamp values, normalize angles
3. **Browser Support**: Older browsers may lack `requestAnimationFrame`
   - Mitigation: Polyfill if needed (unlikely for modern browsers)

**Success Criteria**:
- [ ] Click card → smooth focus animation
- [ ] Focus complete → pulse highlight
- [ ] FOV near target → size overlay appears
- [ ] Color coding matches size ratio
- [ ] No console errors
- [ ] 60 FPS maintained
- [ ] Works in all major browsers

---

**End of Implementation Plan**
