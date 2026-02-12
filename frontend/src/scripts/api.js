// API Service
const API = {
  baseURL: '/api/v1',
  delay: 100,

  async request(endpoint, options = {}) {
    await new Promise(resolve => setTimeout(resolve, this.delay));

    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error?.message || '请求失败');
    }

    return result.data;
  },

  // Locations
  async getCurrentLocation() {
    return this.request('/locations/geolocate', {
      method: 'POST'
    });
  },

  async getSavedLocations() {
    return this.request('/locations');
  },

  async saveLocation(location) {
    return this.request('/locations', {
      method: 'POST',
      body: JSON.stringify(location)
    });
  },

  async deleteLocation(locationId) {
    return this.request(`/locations/${locationId}`, {
      method: 'DELETE'
    });
  },

  // Equipment
  async getEquipmentPresets() {
    return this.request('/equipment/presets');
  },

  async calculateFOV(sensorWidth, sensorHeight, focalLength) {
    return this.request('/equipment/calculate-fov', {
      method: 'POST',
      body: JSON.stringify({
        sensor_width: sensorWidth,
        sensor_height: sensorHeight,
        focal_length: focalLength
      })
    });
  },

  async saveEquipment(equipment) {
    return this.request('/equipment', {
      method: 'POST',
      body: JSON.stringify(equipment)
    });
  },

  // Visible Zones
  async getVisibleZones() {
    return this.request('/visible-zones');
  },

  async saveVisibleZone(zone) {
    return this.request('/visible-zones', {
      method: 'POST',
      body: JSON.stringify(zone)
    });
  },

  async updateVisibleZone(zoneId, zone) {
    return this.request(`/visible-zones/${zoneId}`, {
      method: 'PUT',
      body: JSON.stringify(zone)
    });
  },

  async deleteVisibleZone(zoneId) {
    return this.request(`/visible-zones/${zoneId}`, {
      method: 'DELETE'
    });
  },

  // Targets
  async getDeepskyObjects(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/targets${query ? `?${query}` : ''}`);
  },

  async getDeepskyObject(targetId) {
    return this.request(`/targets/${targetId}`);
  },

  async searchTargets(query) {
    return this.request(`/targets/search?q=${encodeURIComponent(query)}`);
  },

  // Recommendations
  async getRecommendations(params) {
    return this.request('/recommendations', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getRecommendationsByPeriod(period, params) {
    return this.request('/recommendations/by-period', {
      method: 'POST',
      body: JSON.stringify({
        period: period,
        ...params
      })
    });
  },

  async getRecommendationsSummary(params) {
    return this.request('/recommendations/summary', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // Visibility
  async getTargetPosition(targetId, location, timestamp) {
    return this.request('/visibility/position', {
      method: 'POST',
      body: JSON.stringify({
        target_id: targetId,
        location: location,
        timestamp: timestamp.toISOString()
      })
    });
  },

  async getVisibilityWindows(targetId, location, date, visibleZones) {
    return this.request('/visibility/windows', {
      method: 'POST',
      body: JSON.stringify({
        target_id: targetId,
        location: location,
        date: date,
        visible_zones: visibleZones
      })
    });
  },

  async getBatchTargetPositions(targetIds, location, timestamp) {
    return this.request('/visibility/positions-batch', {
      method: 'POST',
      body: JSON.stringify({
        target_ids: targetIds,
        location: location,
        timestamp: timestamp.toISOString()
      })
    });
  },

  // Sky Map
  async getSkyMapData(params) {
    return this.request('/sky-map/data', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getSkyMapTimeline(params) {
    return this.request('/sky-map/timeline', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  // Moon
  async getMoonPosition(params) {
    return this.request('/moon/position', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getMoonHeatmap(params) {
    return this.request('/moon/heatmap', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  },

  async getMoonPollution(params) {
    return this.request('/moon/pollution', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
};

export default API;
