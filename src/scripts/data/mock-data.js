// Mock Data
export const mockData = {
  deepskyObjects: [
    {
      id: "M42",
      name: "猎户座大星云",
      type: "emission-nebula",
      ra: 83.633,
      dec: -5.391,
      magnitude: 4.0,
      size: 85,
      constellation: "Orion",
      difficulty: 1
    },
    {
      id: "M31",
      name: "仙女座星系",
      type: "galaxy",
      ra: 10.684,
      dec: 41.269,
      magnitude: 3.4,
      size: 178,
      constellation: "Andromeda",
      difficulty: 2
    },
    {
      id: "M45",
      name: "昴宿星团",
      type: "cluster",
      ra: 56.63,
      dec: 23.97,
      magnitude: 1.6,
      size: 110,
      constellation: "Taurus",
      difficulty: 1
    },
    {
      id: "M1",
      name: "蟹状星云",
      type: "emission-nebula",
      ra: 83.63,
      dec: 22.02,
      magnitude: 8.4,
      size: 6,
      constellation: "Taurus",
      difficulty: 3
    }
  ],

  equipmentPresets: [
    {
      id: "eq-1",
      name: "全画幅 + 200mm",
      sensor: "full-frame",
      sensorWidth: 36,
      sensorHeight: 24,
      focalLength: 200,
      fovH: 10.3,
      fovV: 6.9
    },
    {
      id: "eq-2",
      name: "APS-C + 85mm",
      sensor: "aps-c",
      sensorWidth: 23.6,
      sensorHeight: 15.6,
      focalLength: 85,
      fovH: 15.2,
      fovV: 10.1
    },
    {
      id: "eq-3",
      name: "M4/3 + 300mm",
      sensor: "m43",
      sensorWidth: 17.3,
      sensorHeight: 13.0,
      focalLength: 300,
      fovH: 4.4,
      fovV: 3.3
    }
  ],

  recommendations: {
    "tonight-golden": [
      {
        targetId: "M42",
        name: "猎户座大星云",
        type: "nebula",
        magnitude: 4.0,
        size: "1° × 0.75°",
        constellation: "Orion",
        bestTime: { start: "20:30", end: "23:45" },
        currentAltitude: 45.2,
        currentAzimuth: 135.6,
        maxAltitude: 65,
        maxAltitudeTime: "22:15",
        score: 92,
        scoreBreakdown: { altitude: 38, brightness: 28, fovMatch: 15, duration: 6 },
        visibilityWindows: [
          {
            startTime: "2025-01-22T20:30:00+08:00",
            endTime: "2025-01-23T00:45:00+08:00",
            maxAltitude: 65,
            zoneId: "zone-1"
          }
        ]
      },
      {
        targetId: "M31",
        name: "仙女座星系",
        type: "galaxy",
        magnitude: 3.4,
        size: "3° × 1°",
        constellation: "Andromeda",
        bestTime: { start: "21:00", end: "01:30" },
        currentAltitude: 32.0,
        currentAzimuth: 30.5,
        maxAltitude: 48,
        maxAltitudeTime: "23:00",
        score: 78,
        scoreBreakdown: { altitude: 30, brightness: 25, fovMatch: 15, duration: 8 },
        visibilityWindows: [
          {
            startTime: "2025-01-22T21:00:00+08:00",
            endTime: "2025-01-23T01:30:00+08:00",
            maxAltitude: 48,
            zoneId: "zone-1"
          }
        ]
      },
      {
        targetId: "M45",
        name: "昴宿星团",
        type: "cluster",
        magnitude: 1.6,
        size: "2° × 2°",
        constellation: "Taurus",
        bestTime: { start: "19:30", end: "22:00" },
        currentAltitude: 58.0,
        currentAzimuth: 240.0,
        maxAltitude: 72,
        maxAltitudeTime: "20:00",
        score: 65,
        scoreBreakdown: { altitude: 35, brightness: 20, fovMatch: 5, duration: 5 },
        visibilityWindows: [
          {
            startTime: "2025-01-22T19:30:00+08:00",
            endTime: "2025-01-22T22:00:00+08:00",
            maxAltitude: 72,
            zoneId: "zone-1"
          }
        ]
      },
      {
        targetId: "M1",
        name: "蟹状星云",
        type: "nebula",
        magnitude: 8.4,
        size: "6' × 4'",
        constellation: "Taurus",
        bestTime: { start: "20:00", end: "23:30" },
        currentAltitude: 28.0,
        currentAzimuth: 180.0,
        maxAltitude: 45,
        maxAltitudeTime: "21:30",
        score: 88,
        scoreBreakdown: { altitude: 32, brightness: 30, fovMatch: 18, duration: 8 },
        visibilityWindows: [
          {
            startTime: "2025-01-22T20:00:00+08:00",
            endTime: "2025-01-22T23:30:00+08:00",
            maxAltitude: 45,
            zoneId: "zone-1"
          }
        ]
      }
    ],
    "midnight": [],
    "dawn": []
  },

  locations: [
    {
      id: "loc-1",
      name: "北京天文馆",
      lat: 39.9042,
      lng: 116.4074
    },
    {
      id: "loc-2",
      name: "紫金山天文台",
      lat: 32.0617,
      lng: 118.8517
    },
    {
      id: "loc-3",
      name: "云南天文台",
      lat: 25.0333,
      lng: 102.7333
    }
  ]
};
