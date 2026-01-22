// Main Entry Point
import { store } from './store.js';
import { SkyMapCanvas } from './utils/canvas.js';
import { mockData } from './data/mock-data.js';

// App State
let skyMap = null;

// Initialize App
function initApp() {
  console.log('AI Skywatcher initializing...');

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

    // Update sky map with mock targets
    updateSkyMapTargets();
  }

  // Load initial recommendations
  loadRecommendations('tonight-golden');

  // Setup event listeners
  setupEventListeners();

  // Start clock
  startClock();

  console.log('AI Skywatcher initialized');
}

// Update Sky Map Targets
function updateSkyMapTargets() {
  if (!skyMap) return;

  const targets = mockData.recommendations['tonight-golden'].map(rec => ({
    id: rec.targetId,
    type: rec.type,
    azimuth: rec.currentAzimuth,
    altitude: rec.currentAltitude
  }));

  skyMap.updateData({ targets });
}

// Load Recommendations
function loadRecommendations(period) {
  const targetsList = document.getElementById('targetsList');
  if (!targetsList) return;

  const recommendations = mockData.recommendations[period] || [];

  targetsList.innerHTML = recommendations.map(rec => {
    const scoreClass = rec.score >= 80 ? 'score-high' :
                       rec.score >= 60 ? 'score-medium' : 'score-low';
    const ratingClass = rec.score >= 80 ? 'rating-excellent' :
                        rec.score >= 60 ? 'rating-good' : 'rating-fair';
    const typeClass = rec.type;

    return `
      <div class="target-card ${scoreClass}" data-target-id="${rec.targetId}">
        <div class="target-header">
          <h3>${rec.name}</h3>
          <span class="target-type ${typeClass}">${getTypeLabel(rec.type)}</span>
        </div>
        <div class="target-details">
          <div><span>星等:</span> <strong>${rec.magnitude}</strong></div>
          <div><span>视大小:</span> <strong>${rec.size}</strong></div>
          <div><span>最佳时段:</span> <strong>${rec.bestTime.start} - ${rec.bestTime.end}</strong></div>
          <div><span>当前高度:</span> <strong>${rec.currentAltitude.toFixed(1)}°</strong></div>
          <div><span>方位角:</span> <strong>${rec.currentAzimuth.toFixed(1)}°</strong></div>
        </div>
        <div class="target-rating">
          <span>推荐指数</span>
          <strong class="${ratingClass}">${rec.score}</strong>
        </div>
        <div class="rating-bar">
          <div class="rating-fill" style="width: ${rec.score}%;
            background: ${rec.score >= 80 ? '#22C55E' : rec.score >= 60 ? '#FACC15' : '#F97316'};">
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
}

// Get Type Label
function getTypeLabel(type) {
  const labels = {
    'nebula': '星云',
    'galaxy': '星系',
    'cluster': '星团'
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
    btnAutoLocation.addEventListener('click', () => {
      console.log('Auto location clicked');
      // TODO: Implement geolocation
      updateDateTime();
    });
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
