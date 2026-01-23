/**
 * LocalStorage Utility for SkyWatcher
 * 用于管理用户设置的本地存储
 */

// Storage Keys
export const STORAGE_KEYS = {
  SAVED_LOCATIONS: 'skywatcher_saved_locations',   // 常用地点列表
  CURRENT_LOCATION: 'skywatcher_current_location', // 当前位置
  SELECTED_EQUIPMENT: 'skywatcher_equipment',      // 设备配置
  SELECTED_DATE: 'skywatcher_date'                 // 选择的日期
};

/**
 * 获取保存的常用地点列表
 * @returns {Array} 常用地点列表
 */
export function getSavedLocations() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.SAVED_LOCATIONS);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Failed to get saved locations:', error);
    return [];
  }
}

/**
 * 保存常用地点列表
 * @param {Array} locations - 常用地点列表
 */
export function saveLocations(locations) {
  try {
    localStorage.setItem(STORAGE_KEYS.SAVED_LOCATIONS, JSON.stringify(locations));
    return true;
  } catch (error) {
    console.error('Failed to save locations:', error);
    return false;
  }
}

/**
 * 添加常用地点
 * @param {Object} location - 地点信息 {name, latitude, longitude, timezone}
 * @returns {Object|null} 添加后的地点对象，失败返回 null
 */
export function addSavedLocation(location) {
  try {
    const locations = getSavedLocations();

    // 生成唯一 ID
    const id = `loc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const newLocation = {
      id,
      name: location.name || '未命名地点',
      latitude: location.latitude,
      longitude: location.longitude,
      timezone: location.timezone || 'Asia/Shanghai',
      createdAt: new Date().toISOString()
    };

    locations.push(newLocation);
    saveLocations(locations);

    return newLocation;
  } catch (error) {
    console.error('Failed to add location:', error);
    return null;
  }
}

/**
 * 删除常用地点
 * @param {string} locationId - 地点 ID
 * @returns {boolean} 是否删除成功
 */
export function deleteSavedLocation(locationId) {
  try {
    const locations = getSavedLocations();
    const filtered = locations.filter(loc => loc.id !== locationId);

    if (filtered.length === locations.length) {
      return false; // 没有找到对应的地点
    }

    saveLocations(filtered);
    return true;
  } catch (error) {
    console.error('Failed to delete location:', error);
    return false;
  }
}

/**
 * 获取当前保存的位置
 * @returns {Object|null} 位置对象
 */
export function getCurrentLocation() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CURRENT_LOCATION);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error('Failed to get current location:', error);
    return null;
  }
}

/**
 * 保存当前位置
 * @param {Object} location - 位置对象 {latitude, longitude, timezone}
 */
export function saveCurrentLocation(location) {
  try {
    localStorage.setItem(STORAGE_KEYS.CURRENT_LOCATION, JSON.stringify(location));
    return true;
  } catch (error) {
    console.error('Failed to save current location:', error);
    return false;
  }
}

/**
 * 获取保存的设备配置
 * @returns {Object|null} 设备配置对象
 */
export function getSavedEquipment() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.SELECTED_EQUIPMENT);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error('Failed to get saved equipment:', error);
    return null;
  }
}

/**
 * 保存设备配置
 * @param {Object} equipment - 设备配置对象
 */
export function saveEquipment(equipment) {
  try {
    localStorage.setItem(STORAGE_KEYS.SELECTED_EQUIPMENT, JSON.stringify(equipment));
    return true;
  } catch (error) {
    console.error('Failed to save equipment:', error);
    return false;
  }
}

/**
 * 获取保存的日期
 * @returns {string|null} 日期字符串 (YYYY-MM-DD)
 */
export function getSavedDate() {
  try {
    return localStorage.getItem(STORAGE_KEYS.SELECTED_DATE);
  } catch (error) {
    console.error('Failed to get saved date:', error);
    return null;
  }
}

/**
 * 保存选择的日期
 * @param {string} date - 日期字符串 (YYYY-MM-DD)
 */
export function saveDate(date) {
  try {
    localStorage.setItem(STORAGE_KEYS.SELECTED_DATE, date);
    return true;
  } catch (error) {
    console.error('Failed to save date:', error);
    return false;
  }
}

/**
 * 清除所有存储数据
 */
export function clearAllStorage() {
  try {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    return true;
  } catch (error) {
    console.error('Failed to clear storage:', error);
    return false;
  }
}
