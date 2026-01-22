// State Management
export class Store {
  constructor(initialState) {
    this.state = initialState;
    this.listeners = [];
  }

  getState() {
    return this.state;
  }

  setState(partialState) {
    this.state = { ...this.state, ...partialState };
    this.notify();
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }
}

// Initial State
export const initialState = {
  config: {
    location: {
      mode: 'manual',
      current: { lat: 39.9042, lng: 116.4074, name: '北京天文馆' },
      saved: [
        { id: 'loc-1', name: '北京天文馆', lat: 39.9042, lng: 116.4074 }
      ]
    },
    equipment: {
      sensor: 'full-frame',
      sensorWidth: 36,
      sensorHeight: 24,
      focalLength: 200,
      fovH: 10.5,
      fovV: 7.0
    },
    visibleZones: []
  },

  skyMap: {
    currentTime: new Date(),
    selectedDate: new Date(),
    hoveredTarget: null,
    selectedTarget: null,
    zoom: 1.0,
    pan: { x: 0, y: 0 }
  },

  recommendations: {
    currentPeriod: 'tonight-golden',
    sortBy: 'score',
    periods: {
      'tonight-golden': [],
      'midnight': [],
      'dawn': []
    }
  },

  ui: {
    isConfigPanelOpen: true,
    isRecommendPanelOpen: true,
    activeModal: null,
    isLoading: false,
    error: null
  }
};

// Create global store instance
export const store = new Store(initialState);
