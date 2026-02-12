// Main Entry Point
import { store } from './store.js';
import { SkyMapCanvas } from './utils/canvas.js';
import API from './api.js';
import {
  getSavedLocations,
  addSavedLocation,
  deleteSavedLocation,
  saveCurrentLocation,
  getCurrentLocation,
  getSavedEquipment,
  saveEquipment,
  getSavedDate,
  saveDate,
  getVisibleZones,
  addRectZone,
  deleteVisibleZone,
  getFOVFramePosition,
  saveFOVFramePosition
} from './utils/storage.js';

// App State
let skyMap = null;
let currentLocation = { latitude: 39.9042, longitude: 116.4074, timezone: 'Asia/Shanghai' };
let currentEquipment = { fov_horizontal: 10.3, fov_vertical: 6.9 };
let equipmentPresets = [];
let currentPresetId = null;
let selectedDate = new Date(); // 用户选择的观测日期
let savedLocations = [];
let selectedLocationId = null; // 当前选中的常用地点 ID

// Initialize App
function initApp() {
  console.log('AI Skywatcher initializing...');

  // Load saved locations from localStorage
  loadSavedLocations();

  // Load saved date
  const savedDate = getSavedDate();
  if (savedDate) {
    selectedDate = new Date(savedDate);
  }

  // Initialize date picker with current date
  initDatePicker();

  // Initialize Sky Map Canvas
  const canvas = document.getElementById('skyMapCanvas');
  if (canvas) {
    // 动态获取容器尺寸
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight || containerWidth; // 如果没有高度，使用宽度（正方形）

    console.log('Canvas container size:', containerWidth, 'x', containerHeight);

    skyMap = new SkyMapCanvas(canvas, {
      width: containerWidth,
      height: containerHeight
    });

    // Set target select callback
    skyMap.onTargetSelect = (targetId) => {
      console.log('Selected target:', targetId);
      // TODO: Scroll to target card in recommend panel
    };

    // Set moon toggle callback
    skyMap.onMoonToggle = (showHeatmap) => {
      console.log('Moon heatmap toggled:', showHeatmap);
      if (showHeatmap) {
        loadMoonHeatmap();
      }
    };

    // Load initial sky map data
    loadSkyMapData();

    // Load initial moon data
    loadMoonData();
  }

  // Load initial recommendations
  loadRecommendations('tonight-golden');

  // Initialize visible zones
  renderZonesList();
  loadZonesToCanvas();

  // Initialize FOV frame
  initFOVFrame();

  // Load equipment presets
  loadEquipmentPresets();

  // Setup event listeners
  setupEventListeners();

  // Start clock
  startClock();

  // Set up moon data updates every 5 minutes
  setInterval(loadMoonData, 5 * 60 * 1000);

  console.log('AI Skywatcher initialized');
}

// Load Saved Locations from localStorage
function loadSavedLocations() {
  savedLocations = getSavedLocations();
  updateLocationSelect();
  console.log('Loaded saved locations:', savedLocations.length);
}

// Update Location Select Dropdown
function updateLocationSelect() {
  const selectLocation = document.getElementById('selectLocation');
  if (!selectLocation) return;

  if (savedLocations.length === 0) {
    selectLocation.innerHTML = '<option value="">常用地点 (0)</option>';
  } else {
    selectLocation.innerHTML = '<option value="">常用地点 (' + savedLocations.length + ')</option>' +
      savedLocations.map(loc =>
        `<option value="${loc.id}">${loc.name}</option>`
      ).join('');
  }
}

// Check if current location exists in saved locations
function isCurrentLocationSaved() {
  if (!currentLocation || selectedLocationId) return false;

  return savedLocations.some(loc =>
    Math.abs(loc.latitude - currentLocation.latitude) < 0.0001 &&
    Math.abs(loc.longitude - currentLocation.longitude) < 0.0001
  );
}

// Show/Hide Save and Delete Buttons
function updateLocationButtons() {
  const btnSaveLocation = document.getElementById('btnSaveLocation');
  const btnDeleteLocation = document.getElementById('btnDeleteLocation');

  if (!btnSaveLocation || !btnDeleteLocation) return;

  // Show save button if current location is not in saved list and no location is selected
  btnSaveLocation.style.display = (!isCurrentLocationSaved() && !selectedLocationId) ? 'inline-flex' : 'none';

  // Show delete button if a saved location is selected
  btnDeleteLocation.style.display = selectedLocationId ? 'inline-flex' : 'none';
}

// Save Current Location to Saved Locations
async function saveCurrentLocationToSaved() {
  const locationName = prompt('请输入地点名称:', '我的观测点');
  if (!locationName || locationName.trim() === '') {
    return;
  }

  const newLocation = addSavedLocation({
    name: locationName.trim(),
    latitude: currentLocation.latitude,
    longitude: currentLocation.longitude,
    timezone: currentLocation.timezone || 'Asia/Shanghai'
  });

  if (newLocation) {
    savedLocations = getSavedLocations();
    updateLocationSelect();
    updateLocationButtons();
    alert(`已保存地点: ${newLocation.name}`);
  } else {
    alert('保存失败，请重试');
  }
}

// Handle Location Selection Change
function handleLocationSelectChange(e) {
  selectedLocationId = e.target.value || null;

  if (selectedLocationId) {
    // Load selected location
    const location = savedLocations.find(loc => loc.id === selectedLocationId);
    if (location) {
      currentLocation = {
        latitude: location.latitude,
        longitude: location.longitude,
        timezone: location.timezone
      };

      // Update UI
      document.getElementById('inputLat').value = location.latitude.toFixed(6);
      document.getElementById('inputLng').value = location.longitude.toFixed(6);

      const locationText = document.querySelector('.location-text');
      if (locationText) {
        locationText.textContent = location.name;
      }

      // Reload recommendations with new location
      loadRecommendations('tonight-golden');

      // Reload sky map and moon data with new location
      loadSkyMapData();
    }
  }

  updateLocationButtons();
}

// Delete Selected Location
function deleteSelectedLocation() {
  if (!selectedLocationId) return;

  const location = savedLocations.find(loc => loc.id === selectedLocationId);
  if (!location) return;

  if (confirm(`确定要删除地点 "${location.name}" 吗?`)) {
    const success = deleteSavedLocation(selectedLocationId);
    if (success) {
      savedLocations = getSavedLocations();
      selectedLocationId = null;
      updateLocationSelect();
      updateLocationButtons();
      alert('地点已删除');
    } else {
      alert('删除失败，请重试');
    }
  }
}

// Handle Manual Location Input
function handleLocationInput() {
  const inputLat = document.getElementById('inputLat');
  const inputLng = document.getElementById('inputLng');

  if (!inputLat || !inputLng) return;

  const lat = parseFloat(inputLat.value);
  const lng = parseFloat(inputLng.value);

  // Validate input
  if (isNaN(lat) || isNaN(lng) ||
      lat < -90 || lat > 90 ||
      lng < -180 || lng > 180) {
    return; // Invalid input, don't update
  }

  // Update current location with manual input
  currentLocation = {
    latitude: lat,
    longitude: lng,
    timezone: currentLocation?.timezone || 'Asia/Shanghai'
  };

  // Clear selected location when manually inputting
  if (selectedLocationId) {
    selectedLocationId = null;
    const selectLocation = document.getElementById('selectLocation');
    if (selectLocation) {
      selectLocation.value = '';
    }
  }

  // Update location text to show manual input
  const locationText = document.querySelector('.location-text');
  if (locationText) {
    locationText.textContent = '手动输入';
  }

  // Update save/delete buttons
  updateLocationButtons();

  // Reload sky map and moon data with new location
  loadSkyMapData();

  console.log('Location manually updated:', { lat, lng });
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
    name: rec.target.name,
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
        name: t.name,
        type: t.type,
        azimuth: t.azimuth,
        altitude: t.altitude
      }));

      skyMap.updateData({ targets });
    }

    // Update moon position for selected date
    await loadMoonData(timestamp);
  } catch (error) {
    console.error('Failed to load sky map data:', error);
  }
}

// Load Moon Data
async function loadMoonData(timestamp = null) {
  try {
    const time = timestamp || new Date();

    const data = await API.getMoonPosition({
      location: currentLocation,
      timestamp: time.toISOString()
    });

    if (skyMap && data.position) {
      skyMap.updateData({
        moon: {
          position: {
            azimuth: data.position.azimuth,
            altitude: data.position.altitude,
            distance: data.position.distance,
            ra: data.position.ra,
            dec: data.position.dec
          },
          phase: data.phase,
          visible: data.position.altitude > 0
        }
      });
    }

    console.log('Moon data loaded:', data);
  } catch (error) {
    console.error('Failed to load moon data:', error);
  }
}

// Load Moon Heatmap
async function loadMoonHeatmap(timestamp = null) {
  try {
    const time = timestamp || new Date();

    const data = await API.getMoonHeatmap({
      location: currentLocation,
      timestamp: time.toISOString(),
      resolution: 36
    });

    if (skyMap && data.heatmap) {
      skyMap.updateData({
        moon: {
          showHeatmap: true,
          heatmapData: data.heatmap
        }
      });
    }

    console.log('Moon heatmap loaded');
  } catch (error) {
    console.error('Failed to load moon heatmap:', error);
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

    // Update FOV frame size
    if (skyMap) {
      skyMap.updateFOVFrameSize(
        currentEquipment.fov_horizontal,
        currentEquipment.fov_vertical
      );
    }

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

      // Update FOV frame size
      if (skyMap) {
        skyMap.updateFOVFrameSize(
          currentEquipment.fov_horizontal,
          currentEquipment.fov_vertical
        );
      }

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

    // Load visible zones from localStorage and convert to polygon format
    const visibleZones = getVisibleZones().map(zone => ({
      id: zone.id,
      name: zone.name,
      polygon: [
        zone.start,
        [zone.end[0], zone.start[1]],
        zone.end,
        [zone.start[0], zone.end[1]]
      ],
      priority: zone.priority
    }));

    const data = await API.getRecommendations({
      location: currentLocation,
      date: selectedDateStr,
      equipment: currentEquipment,
      visible_zones: visibleZones,
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

      // Get moonlight impact
      let moonlightImpact = null;
      let moonlightImpactClass = '';
      let moonlightColor = '';
      if (rec.score_breakdown && rec.score_breakdown.moonlight_impact !== undefined) {
        const pollution = rec.score_breakdown.moonlight_impact;
        const pollutionPercent = Math.round(pollution * 100);

        if (pollution <= 0.1) {
          moonlightImpact = { level: '无影响', percentage: pollutionPercent };
          moonlightImpactClass = 'impact-none';
          moonlightColor = '#22C55E';
        } else if (pollution <= 0.3) {
          moonlightImpact = { level: '轻微', percentage: pollutionPercent };
          moonlightImpactClass = 'impact-low';
          moonlightColor = '#FACC15';
        } else if (pollution <= 0.5) {
          moonlightImpact = { level: '中等', percentage: pollutionPercent };
          moonlightImpactClass = 'impact-medium';
          moonlightColor = '#FB923C';
        } else if (pollution <= 0.7) {
          moonlightImpact = { level: '严重', percentage: pollutionPercent };
          moonlightImpactClass = 'impact-high';
          moonlightColor = '#F97316';
        } else {
          moonlightImpact = { level: '极严重', percentage: pollutionPercent };
          moonlightImpactClass = 'impact-severe';
          moonlightColor = '#EF4444';
        }
      }

      const moonlightHtml = moonlightImpact ? `
        <div class="moonlight-impact ${moonlightImpactClass}">
          <span>月光影响:</span>
          <strong style="color: ${moonlightColor}">${moonlightImpact.level} (${moonlightImpact.percentage}%)</strong>
        </div>
      ` : '';

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
            ${moonlightHtml}
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
  // Add zone button
  const btnAddZone = document.getElementById('btnAddZone');
  if (btnAddZone) {
    btnAddZone.addEventListener('click', addNewZone);
  }

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

          // Clear selected location when using auto-location
          selectedLocationId = null;
          document.getElementById('selectLocation').value = '';

          // Update save/delete buttons
          updateLocationButtons();

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

  // Location input fields - handle manual input
  const inputLat = document.getElementById('inputLat');
  const inputLng = document.getElementById('inputLng');

  if (inputLat) {
    inputLat.addEventListener('input', debounce(handleLocationInput, 300));
  }

  if (inputLng) {
    inputLng.addEventListener('input', debounce(handleLocationInput, 300));
  }

  // Timeline slider
  const timelineSlider = document.getElementById('timelineSlider');
  if (timelineSlider) {
    // 监听滑块input事件
    timelineSlider.addEventListener('input', (e) => {
      updateTimelineFromSlider(e.target.value);
    });
  }

  // Saved location select
  const selectLocation = document.getElementById('selectLocation');
  if (selectLocation) {
    selectLocation.addEventListener('change', handleLocationSelectChange);
  }

  // Save location button
  const btnSaveLocation = document.getElementById('btnSaveLocation');
  if (btnSaveLocation) {
    btnSaveLocation.addEventListener('click', saveCurrentLocationToSaved);
  }

  // Delete location button
  const btnDeleteLocation = document.getElementById('btnDeleteLocation');
  if (btnDeleteLocation) {
    btnDeleteLocation.addEventListener('click', deleteSelectedLocation);
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

// Update Timeline from Event (保留旧函数以备兼容)
function updateTimelineFromEvent(e) {
  const timelineBar = document.querySelector('.timeline-bar');
  const rect = timelineBar.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));

  const timelineProgress = document.getElementById('timelineProgress');
  const timelineTime = document.getElementById('timelineTime');
  const timelineSlider = document.getElementById('timelineSlider');

  if (timelineProgress) {
    timelineProgress.style.width = `${percentage}%`;
  }

  // 同步滑块位置
  if (timelineSlider) {
    timelineSlider.value = percentage;
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

  // Update sky map with new time
  updateSkyMapForTime(hour, minute);
}

// Update Timeline from Slider
function updateTimelineFromSlider(sliderValue) {
  const percentage = parseFloat(sliderValue);

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

  // Update sky map with new time
  updateSkyMapForTime(hour, minute);
}

// Update Sky Map for specific time
let updateSkyMapTimeout = null;
function updateSkyMapForTime(hour, minute) {
  // Clear previous timeout
  if (updateSkyMapTimeout) {
    clearTimeout(updateSkyMapTimeout);
  }

  // Debounce the update to avoid too many API calls
  updateSkyMapTimeout = setTimeout(async () => {
    try {
      // Create timestamp for selected date at specified time
      const timestamp = new Date(selectedDate);
      timestamp.setHours(hour, minute, 0, 0);

      // Get sky map data for new time
      const data = await API.getSkyMapData({
        location: currentLocation,
        timestamp: timestamp.toISOString(),
        include_targets: true,
        target_types: ['emission-nebula', 'galaxy', 'cluster', 'planetary-nebula']
      });

      if (skyMap && data.targets) {
        const targets = data.targets.map(t => ({
          id: t.id,
          name: t.name,
          type: t.type,
          azimuth: t.azimuth,
          altitude: t.altitude
        }));

        skyMap.updateData({ targets });
      }

      // Update moon position for new time
      await loadMoonData(timestamp);
    } catch (error) {
      console.error('Failed to update sky map for time:', error);
    }
  }, 100); // 100ms debounce

  // FOV 框开关
  const chkShowFOV = document.getElementById('chkShowFOV');
  if (chkShowFOV) {
    chkShowFOV.addEventListener('change', (e) => {
      skyMap?.setFOVFrameVisible(e.target.checked);
    });
  }

  // 重置 FOV 位置
  const btnResetFOV = document.getElementById('btnResetFOV');
  if (btnResetFOV) {
    btnResetFOV.addEventListener('click', () => {
      skyMap?.setFOVFrameCenter(180, 45);
      saveFOVFramePosition({ azimuth: 180, altitude: 45 });
    });
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

// ========== 可视区域管理 ==========

/**
 * 渲染可视区域列表
 */
function renderZonesList() {
  const zonesList = document.getElementById('zonesList');
  if (!zonesList) return;

  const zones = getVisibleZones();

  zonesList.innerHTML = zones.map(zone => {
    const [startAz, startAlt] = zone.start;
    const [endAz, endAlt] = zone.end;
    const rangeText = `Az: ${startAz}°-${endAz}°, Alt: ${startAlt}°-${endAlt}°`;

    return `
      <div class="zone-item ${zone.isDefault ? 'default' : ''}" data-zone-id="${zone.id}">
        <div class="zone-info">
          <div class="zone-name">${zone.name}</div>
          <div class="zone-range">${rangeText}</div>
        </div>
        <button class="zone-delete ${zone.isDefault ? 'default' : ''}"
                data-zone-id="${zone.id}"
                title="删除区域">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
    `;
  }).join('');

  // 绑定删除按钮事件
  zonesList.querySelectorAll('.zone-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const zoneId = e.currentTarget.dataset.zoneId;
      if (zoneId && confirm('确定要删除这个区域吗？')) {
        deleteVisibleZone(zoneId);
        renderZonesList();
        loadZonesToCanvas();
        loadRecommendations('tonight-golden');
      }
    });
  });
}

/**
 * 添加新区域
 */
function addNewZone() {
  const startAz = parseFloat(document.getElementById('zoneStartAz').value);
  const startAlt = parseFloat(document.getElementById('zoneStartAlt').value);
  const endAz = parseFloat(document.getElementById('zoneEndAz').value);
  const endAlt = parseFloat(document.getElementById('zoneEndAlt').value);
  const name = document.getElementById('zoneName').value.trim();

  // 验证输入
  if (isNaN(startAz) || isNaN(startAlt) || isNaN(endAz) || isNaN(endAlt)) {
    alert('请输入有效的坐标值');
    return;
  }

  if (startAz >= endAz || startAlt >= endAlt) {
    alert('起始值必须小于结束值');
    return;
  }

  if (!name) {
    alert('请输入区域名称');
    return;
  }

  // 添加区域
  const zone = addRectZone(name, startAz, startAlt, endAz, endAlt);

  if (zone) {
    // 清空表单
    document.getElementById('zoneName').value = '';

    // 刷新列表
    renderZonesList();

    // 更新Canvas
    loadZonesToCanvas();

    // 刷新推荐
    loadRecommendations('tonight-golden');

    alert(`区域 "${name}" 已添加`);
  } else {
    alert('添加区域失败，请重试');
  }
}

/**
 * 加载可视区域到Canvas
 */
function loadZonesToCanvas() {
  if (!skyMap) return;

  const zones = getVisibleZones();
  skyMap.updateData({ zones });
  skyMap.render();
}

/**
 * 初始化 FOV 框
 */
function initFOVFrame() {
  if (!skyMap) return;

  // 加载保存的位置
  const savedPos = getFOVFramePosition();
  skyMap.setFOVFrameCenter(savedPos.azimuth, savedPos.altitude);

  // 设置当前 FOV 大小
  if (currentEquipment && currentEquipment.fov_horizontal) {
    skyMap.updateFOVFrameSize(
      currentEquipment.fov_horizontal,
      currentEquipment.fov_vertical
    );
  }

  // 防抖函数
  const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  };

  // 绑定移动事件（保存位置）
  skyMap.onFOVFrameMove = debounce((center) => {
    saveFOVFramePosition(center);
  }, 500);

  skyMap.onFOVFrameChange = (center) => {
    saveFOVFramePosition(center);
  };
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
