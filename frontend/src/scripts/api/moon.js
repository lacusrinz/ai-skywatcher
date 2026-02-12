/**
 * Moon API Wrapper
 * Provides methods to interact with the Moon API endpoints
 */
export class MoonAPI {
  /**
   * Get moon position data
   * @param {number} lat - Observer latitude
   * @param {number} lon - Observer longitude
   * @param {string} timestamp - ISO 8601 timestamp string (optional)
   * @returns {Promise<Object>} Moon position data
   */
  static async getPosition(lat, lon, timestamp) {
    const response = await fetch('/api/v1/moon/position', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        location: {
          latitude: lat,
          longitude: lon
        },
        timestamp: timestamp || null
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'Failed to get moon position');
    }

    return result.data;
  }

  /**
   * Get moonlight pollution heatmap
   * @param {number} lat - Observer latitude
   * @param {number} lon - Observer longitude
   * @param {string} timestamp - ISO 8601 timestamp string (optional)
   * @param {number} resolution - Heatmap resolution (10-100, default 36)
   * @returns {Promise<Object>} Heatmap data
   */
  static async getHeatmap(lat, lon, timestamp, resolution = 36) {
    const response = await fetch('/api/v1/moon/heatmap', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        location: {
          latitude: lat,
          longitude: lon
        },
        timestamp: timestamp || null,
        resolution: resolution
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'Failed to get heatmap');
    }

    return result.data;
  }

  /**
   * Get moonlight pollution for a specific target
   * @param {number} lat - Observer latitude
   * @param {number} lon - Observer longitude
   * @param {string} timestamp - ISO 8601 timestamp string (optional)
   * @param {number} targetAlt - Target altitude in degrees
   * @param {number} targetAz - Target azimuth in degrees
   * @returns {Promise<Object>} Pollution data
   */
  static async getPollution(lat, lon, timestamp, targetAlt, targetAz) {
    const response = await fetch('/api/v1/moon/pollution', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        location: {
          latitude: lat,
          longitude: lon
        },
        timestamp: timestamp || null,
        target_position: {
          altitude: targetAlt,
          azimuth: targetAz
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'Failed to get pollution data');
    }

    return result.data;
  }
}

export default MoonAPI;
