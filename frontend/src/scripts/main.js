// Main Entry Point
import { store } from './store.js';
import { SkyMapCanvas } from './utils/canvas.js';
import API from './api.js';

// App State
let skyMap = null;
let currentLocation = { latitude: 39.9042, longitude: 116.4074, timezone: 'Asia/Shanghai' };
let currentEquipment = { fov_horizontal: 10.3, fov_vertical: 6.9 };
let equipmentPresets = [];
let currentPresetId = null;
let selectedDate = new Date(); // 用户选择的观测日期

// Initialize App
function initApp() {
  console.log('AI Skywatcher initializing...');

  // Initialize date picker with current date
  initDatePicker();

  // Initialize Sky Map Canvas
  const canvas = document.getElementById('skyMapCanvas');
  if (canvas) {
    skyMap = new SkyMapCanvas(canvas, {
      width: 800,
      height: 800
    });

    // Set target select callback
    skyMap.onTargetSelect = (targetId) => {
      console.log('Selected target:', targetId);
      // TODO: Scroll to target card in recommend panel
    };

    // Load initial sky map data
    loadSkyMapData();
  }

  // Load initial recommendations
  loadRecommendations('tonight-golden');

  // Load equipment presets
  loadEquipmentPresets();

  // Setup event listeners
  setupEventListeners();

  // Start clock
  startClock();

  console.log('AI Skywatcher initialized');
}

// Initialize Date Picker
function initDatePicker() {
  const datePicker = document.getElementById('datePicker');
  if (datePicker) {
    // Set default date to today
    const today = new Date();
    const formattedDate = formatDateForInput(today);
    datePicker.value = formattedDate;

    // Add change event listener
    datePicker.addEventListener('change', handleDateChange);

    console.log('Date picker initialized with:', formattedDate);
  }
}

// Format Date for Input (YYYY-MM-DD)
function formatDateForInput(date) {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Handle Date Change
function handleDateChange(e) {
  const newDate = new Date(e.target.value);
  if (isNaN(newDate.getTime())) {
    console.error('Invalid date selected');
    return;
  }

  selectedDate = newDate;
  console.log('Date changed to:', formatDateForInput(selectedDate));

  // Reload recommendations with new date
  loadRecommendations('tonight-golden');

  // Reload sky map data with new date
  loadSkyMapData();
}

// Update Sky Map Targets
function updateSkyMapTargets(recommendations) {
  if (!skyMap) return;

  const targets = recommendations.map(rec => ({
    id: rec.target.id,
    type: rec.target.type,
    azimuth: rec.current_position.azimuth,
    altitude: rec.current_position.altitude
  }));

  skyMap.updateData({ targets });
}

// Load Sky Map Data
async function loadSkyMapData() {
  try {
    // Create timestamp from selected date at 20:00 (golden hour)
    const timestamp = new Date(selectedDate);
    timestamp.setHours(20, 0, 0, 0);

    const data = await API.getSkyMapData({
      location: currentLocation,
      timestamp: timestamp.toISOString(),
      include_targets: true,
      target_types: ['emission-nebula', 'galaxy', 'cluster', 'planetary-nebula']
    });

    if (skyMap && data.targets) {
      const targets = data.targets.map(t => ({
        id: t.id,
        type: t.type,
        azimuth: t.azimuth,
        altitude: t.altitude
      }));

      skyMap.updateData({ targets });
    }
  } catch (error) {
    console.error('Failed to load sky map data:', error);
  }
}

// Load Equipment Presets
async function loadEquipmentPresets() {
  try {
    const presets = await API.getEquipmentPresets();
    const selectEquipment = document.getElementById('selectEquipment');

    if (selectEquipment && presets) {
      // Store presets globally
      equipmentPresets = [...presets];

      // Add custom option
      equipmentPresets.push({
        id: 'custom',
        name: '自定义',
        sensor_width: 0,
        sensor_height: 0,
        focal_length: 0,
        fov_horizontal: 0,
        fov_vertical: 0
      });

      selectEquipment.innerHTML = equipmentPresets.map(preset =>
        `<option value="${preset.id}">${preset.name}</option>`
      ).join('');

      // Set default to first preset
      if (equipmentPresets.length > 0) {
        currentPresetId = equipmentPresets[0].id;
        currentEquipment = {
          fov_horizontal: equipmentPresets[0].fov_horizontal,
          fov_vertical: equipmentPresets[0].fov_vertical
        };

        // Update input fields
        updateEquipmentInputs(equipmentPresets[0]);

        // Set input disabled state
        setInputsDisabled(false);

        updateFOVDisplay();
      }

      // Add change event listener
      selectEquipment.addEventListener('change', handleEquipmentPresetChange);
    }
  } catch (error) {
    console.error('Failed to load equipment presets:', error);
  }
}

// Handle Equipment Preset Change
async function handleEquipmentPresetChange(e) {
  const presetId = e.target.value;
  currentPresetId = presetId;

  const preset = equipmentPresets.find(p => p.id === presetId);
  if (!preset) return;

  if (presetId === 'custom') {
    // Enable input fields for custom mode
    setInputsDisabled(true);

    // Clear inputs for custom entry
    document.getElementById('inputSensorWidth').value = '';
    document.getElementById('inputSensorHeight').value = '';
    document.getElementById('inputFocal').value = '';

    // Reset FOV display
    currentEquipment = { fov_horizontal: 0, fov_vertical: 0 };
    updateFOVDisplay();
  } else {
    // Disable input fields for preset mode
    setInputsDisabled(false);

    // Update input fields with preset values
    updateEquipmentInputs(preset);

    // Update current equipment
    currentEquipment = {
      fov_horizontal: preset.fov_horizontal,
      fov_vertical: preset.fov_vertical
    };

    updateFOVDisplay();

    // Reload recommendations with new equipment
    loadRecommendations('tonight-golden');
  }
}

// Update Equipment Input Fields
function updateEquipmentInputs(preset) {
  const inputSensorWidth = document.getElementById('inputSensorWidth');
  const inputSensorHeight = document.getElementById('inputSensorHeight');
  const inputFocal = document.getElementById('inputFocal');

  if (inputSensorWidth && inputSensorHeight && inputFocal) {
    inputSensorWidth.value = preset.sensor_width;
    inputSensorHeight.value = preset.sensor_height;
    inputFocal.value = preset.focal_length;
  }
}

// Set Input Fields Disabled State
function setInputsDisabled(enabled) {
  const inputSensorWidth = document.getElementById('inputSensorWidth');
  const inputSensorHeight = document.getElementById('inputSensorHeight');
  const inputFocal = document.getElementById('inputFocal');

  if (inputSensorWidth && inputSensorHeight && inputFocal) {
    inputSensorWidth.disabled = !enabled;
    inputSensorHeight.disabled = !enabled;
    inputFocal.disabled = !enabled;
  }
}

// Calculate FOV from Input
async function calculateFOVFromInput() {
  if (currentPresetId !== 'custom') return;

  const sensorWidth = parseFloat(document.getElementById('inputSensorWidth').value) || 0;
  const sensorHeight = parseFloat(document.getElementById('inputSensorHeight').value) || 0;
  const focalLength = parseFloat(document.getElementById('inputFocal').value) || 0;

  if (sensorWidth > 0 && sensorHeight > 0 && focalLength > 0) {
    try {
      const result = await API.calculateFOV(sensorWidth, sensorHeight, focalLength);
      currentEquipment = {
        fov_horizontal: result.fov_horizontal,
        fov_vertical: result.fov_vertical
      };
      updateFOVDisplay();

      // Reload recommendations with new equipment
      loadRecommendations('tonight-golden');
    } catch (error) {
      console.error('Failed to calculate FOV:', error);
    }
  }
}

// Update FOV Display
function updateFOVDisplay() {
  const fovPreview = document.querySelector('.fov-preview span');
  if (fovPreview) {
    fovPreview.textContent = `视野范围: ${currentEquipment.fov_horizontal.toFixed(1)}° × ${currentEquipment.fov_vertical.toFixed(1)}°`;
  }
}

// Load Recommendations
async function loadRecommendations(period) {
  const targetsList = document.getElementById('targetsList');
  if (!targetsList) return;

  // Show loading state
  targetsList.innerHTML = '<div class="loading">加载中...</div>';

  try {
    // Use selected date instead of current date
    const selectedDateStr = formatDateForInput(selectedDate);
    const data = await API.getRecommendations({
      location: currentLocation,
      date: selectedDateStr,
      equipment: currentEquipment,
      visible_zones: [
        {
          id: 'all_sky',
          name: '全天空',
          polygon: [[0, 15], [90, 15], [180, 15], [270, 15], [359, 15], [359, 90], [270, 90], [180, 90], [90, 90], [0, 90]],
          priority: 1
        }
      ],
      filters: {
        min_magnitude: 9
      },
      sort_by: 'score',
      limit: 20
    });

    const recommendations = data.recommendations || [];

    // Update sky map with new targets
    updateSkyMapTargets(recommendations);

    // Render target cards
    targetsList.innerHTML = recommendations.map(rec => {
      const score = rec.score || 0;
      const scoreClass = score >= 80 ? 'score-high' :
                         score >= 60 ? 'score-medium' : 'score-low';
      const ratingClass = score >= 80 ? 'rating-excellent' :
                          score >= 60 ? 'rating-good' : 'rating-fair';

      // Get best time from visibility windows
      let bestTime = { start: '--:--', end: '--:--' };
      if (rec.visibility_windows && rec.visibility_windows.length > 0) {
        const window = rec.visibility_windows[0];
        const start = new Date(window.start_time);
        const end = new Date(window.end_time);
        bestTime = {
          start: `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')}`,
          end: `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
        };
      }

      return `
        <div class="target-card ${scoreClass}" data-target-id="${rec.target.id}">
          <div class="target-header">
            <h3>${rec.target.name}</h3>
            <span class="target-type ${rec.target.type}">${getTypeLabel(rec.target.type)}</span>
          </div>
          <div class="target-details">
            <div><span>星等:</span> <strong>${rec.target.magnitude}</strong></div>
            <div><span>视大小:</span> <strong>${rec.target.size}'</strong></div>
            <div><span>最佳时段:</span> <strong>${bestTime.start} - ${bestTime.end}</strong></div>
            <div><span>当前高度:</span> <strong>${rec.current_position.altitude.toFixed(1)}°</strong></div>
            <div><span>方位角:</span> <strong>${rec.current_position.azimuth.toFixed(1)}°</strong></div>
          </div>
          <div class="target-rating">
            <span>推荐指数</span>
            <strong class="${ratingClass}">${score}</strong>
          </div>
          <div class="rating-bar">
            <div class="rating-fill" style="width: ${Math.min(100, score)}%;
              background: ${score >= 80 ? '#22C55E' : score >= 60 ? '#FACC15' : '#F97316'};">
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Add click handlers to target cards
    document.querySelectorAll('.target-card').forEach(card => {
      card.addEventListener('click', () => {
        const targetId = card.dataset.targetId;
        console.log('Clicked target:', targetId);
        // TODO: Show target details
      });
    });

  } catch (error) {
    console.error('Failed to load recommendations:', error);
    targetsList.innerHTML = '<div class="error">加载失败，请重试</div>';
  }
}

// Get Type Label
function getTypeLabel(type) {
  const labels = {
    'emission-nebula': '发射星云',
    'galaxy': '星系',
    'cluster': '星团',
    'planetary-nebula': '行星状星云',
    'supernova-remnant': '超新星遗迹'
  };
  return labels[type] || type;
}

// Setup Event Listeners
function setupEventListeners() {
  // Time filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const period = btn.dataset.period;
      loadRecommendations(period);
    });
  });

  // Auto location button
  const btnAutoLocation = document.getElementById('btnAutoLocation');
  if (btnAutoLocation) {
    btnAutoLocation.addEventListener('click', async () => {
      console.log('Auto location clicked');

      // Show loading state
      btnAutoLocation.disabled = true;
      btnAutoLocation.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="spin">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="30" stroke-dashoffset="10"/>
        </svg>
        定位中...
      `;

      try {
        // Try browser geolocation first
        if (navigator.geolocation) {
          const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              resolve,
              reject,
              {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
              }
            );
          });

          const { latitude, longitude } = position.coords;

          // Get timezone and location info from backend API
          const locationInfo = await API.getCurrentLocation();

          currentLocation = {
            latitude: latitude,
            longitude: longitude,
            timezone: locationInfo.timezone || 'Asia/Shanghai'
          };

          // Update UI
          const locationText = document.querySelector('.location-text');
          if (locationText) {
            locationText.textContent = `${locationInfo.region || '当前位置'} ${locationInfo.country || ''}`;
          }

          document.getElementById('inputLat').value = latitude.toFixed(6);
          document.getElementById('inputLng').value = longitude.toFixed(6);

          console.log('Browser geolocation successful:', { latitude, longitude });
        } else {
          // Fallback to backend mock location
          const location = await API.getCurrentLocation();
          currentLocation = {
            latitude: location.latitude,
            longitude: location.longitude,
            timezone: location.timezone
          };

          // Update UI
          const locationText = document.querySelector('.location-text');
          if (locationText) {
            locationText.textContent = `${location.region || ''} ${location.country || ''}`;
          }

          document.getElementById('inputLat').value = location.latitude;
          document.getElementById('inputLng').value = location.longitude;

          console.log('Using backend fallback location');
        }

        // Reload recommendations with new location
        loadRecommendations('tonight-golden');

      } catch (error) {
        console.error('Failed to get location:', error);

        // Show error message to user
        const locationText = document.querySelector('.location-text');
        if (locationText) {
          locationText.textContent = '定位失败';
        }

        // Use fallback location (Beijing)
        const fallbackLocation = await API.getCurrentLocation();
        currentLocation = {
          latitude: fallbackLocation.latitude,
          longitude: fallbackLocation.longitude,
          timezone: fallbackLocation.timezone
        };

        document.getElementById('inputLat').value = fallbackLocation.latitude;
        document.getElementById('inputLng').value = fallbackLocation.longitude;

        // Update UI after a delay
        setTimeout(() => {
          const locationText = document.querySelector('.location-text');
          if (locationText) {
            locationText.textContent = `${fallbackLocation.region || ''} ${fallbackLocation.country || ''}`;
          }
        }, 2000);
      } finally {
        // Restore button
        btnAutoLocation.disabled = false;
        btnAutoLocation.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 2C6.34 2 5 3.34 5 5c0 1.5 2 4 3 5.5C9 9 11 6.5 11 5c0-1.66-1.34-3-3-3zm0 4c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/>
          </svg>
          自动定位
        `;
      }
    });
  }

  // Equipment input fields - calculate FOV on change (for custom mode)
  const inputSensorWidth = document.getElementById('inputSensorWidth');
  const inputSensorHeight = document.getElementById('inputSensorHeight');
  const inputFocal = document.getElementById('inputFocal');

  if (inputSensorWidth) {
    inputSensorWidth.addEventListener('input', debounce(calculateFOVFromInput, 500));
  }

  if (inputSensorHeight) {
    inputSensorHeight.addEventListener('input', debounce(calculateFOVFromInput, 500));
  }

  if (inputFocal) {
    inputFocal.addEventListener('input', debounce(calculateFOVFromInput, 500));
  }

  // Timeline bar
  const timelineBar = document.querySelector('.timeline-bar');
  if (timelineBar) {
    let isDragging = false;

    timelineBar.addEventListener('mousedown', (e) => {
      isDragging = true;
      updateTimelineFromEvent(e);
    });

    document.addEventListener('mousemove', (e) => {
      if (isDragging) {
        updateTimelineFromEvent(e);
      }
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }
}

// Debounce helper function
function debounce(fn, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}

// Update Timeline from Event
function updateTimelineFromEvent(e) {
  const timelineBar = document.querySelector('.timeline-bar');
  const rect = timelineBar.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));

  const timelineProgress = document.getElementById('timelineProgress');
  const timelineTime = document.getElementById('timelineTime');

  if (timelineProgress) {
    timelineProgress.style.width = `${percentage}%`;
  }

  // Calculate time from percentage (20:00 - 06:00)
  const startHour = 20;
  const totalHours = 10;
  const currentHour = startHour + (percentage / 100) * totalHours;
  const hour = Math.floor(currentHour) % 24;
  const minute = Math.floor((currentHour % 1) * 60);

  if (timelineTime) {
    timelineTime.textContent = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  }
}

// Start Clock
function startClock() {
  updateDateTime();
  setInterval(updateDateTime, 1000);
}

// Update Date Time
function updateDateTime() {
  const now = new Date();
  const datetimeInfo = document.querySelector('.datetime-info');

  if (datetimeInfo) {
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const second = now.getSeconds().toString().padStart(2, '0');

    datetimeInfo.textContent = `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
