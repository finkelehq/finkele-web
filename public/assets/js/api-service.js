/ ============================================
// FILE: public/assets/js/api-service.js
// ============================================

/**
 * Finkele API Service
 * Handles all API calls and data management
 */

class APIService {
    constructor() {
        this.baseURLs = {
            openMeteo: 'https://api.open-meteo.com/v1',
            noaa: 'https://www.ncei.noaa.gov/cdo-web/api/v2',
            climateTrace: 'https://api.climatetrace.org/v1'
        };
        
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Fetch weather data from Open-Meteo API
     */
    async getWeatherData(latitude, longitude) {
        const cacheKey = `weather_${latitude}_${longitude}`;
        
        // Check cache
        if (this.isCacheValid(cacheKey)) {
            return this.cache.get(cacheKey).data;
        }
        
        try {
            const response = await fetch(
                `${this.baseURLs.openMeteo}/forecast?` +
                `latitude=${latitude}&longitude=${longitude}&` +
                `current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&` +
                `hourly=temperature_2m,precipitation_probability,wind_speed_10m&` +
                `daily=temperature_2m_max,temperature_2m_min,precipitation_sum`
            );
            
            if (!response.ok) throw new Error('Weather API request failed');
            
            const data = await response.json();
            
            // Cache the data
            this.setCache(cacheKey, data);
            
            return data;
        } catch (error) {
            console.error('Error fetching weather data:', error);
            return null;
        }
    }

    /**
     * Get climate risk data for a region
     */
    async getClimateRiskData(region) {
        const cacheKey = `risk_${region}`;
        
        if (this.isCacheValid(cacheKey)) {
            return this.cache.get(cacheKey).data;
        }
        
        // Simulate API call with mock data
        const mockData = {
            region: region,
            riskIndex: Math.random() * 100,
            factors: {
                temperature: Math.random() * 5,
                precipitation: Math.random() * 200,
                extremeEvents: Math.floor(Math.random() * 50),
                seaLevel: Math.random() * 2
            },
            timestamp: new Date().toISOString()
        };
        
        this.setCache(cacheKey, mockData);
        return mockData;
    }

    /**
     * Get historical climate data
     */
    async getHistoricalData(latitude, longitude, startDate, endDate) {
        const cacheKey = `historical_${latitude}_${longitude}_${startDate}_${endDate}`;
        
        if (this.isCacheValid(cacheKey)) {
            return this.cache.get(cacheKey).data;
        }
        
        try {
            const response = await fetch(
                `${this.baseURLs.openMeteo}/archive?` +
                `latitude=${latitude}&longitude=${longitude}&` +
                `start_date=${startDate}&end_date=${endDate}&` +
                `daily=temperature_2m_max,temperature_2m_min,precipitation_sum`
            );
            
            if (!response.ok) throw new Error('Historical API request failed');
            
            const data = await response.json();
            this.setCache(cacheKey, data);
            
            return data;
        } catch (error) {
            console.error('Error fetching historical data:', error);
            return null;
        }
    }

    /**
     * Get emissions data
     */
    async getEmissionsData(country, sector) {
        const cacheKey = `emissions_${country}_${sector}`;
        
        if (this.isCacheValid(cacheKey)) {
            return this.cache.get(cacheKey).data;
        }
        
        // Mock emissions data
        const mockData = {
            country: country,
            sector: sector,
            emissions: {
                co2: Math.random() * 1000000,
                ch4: Math.random() * 100000,
                n2o: Math.random() * 10000
            },
            trend: Math.random() > 0.5 ? 'increasing' : 'decreasing',
            year: 2024
        };
        
        this.setCache(cacheKey, mockData);
        return mockData;
    }

    /**
     * Get multiple locations weather data
     */
    async getMultiLocationWeather(locations) {
        const promises = locations.map(loc => 
            this.getWeatherData(loc.latitude, loc.longitude)
        );
        
        try {
            const results = await Promise.all(promises);
            return results.map((data, index) => ({
                ...locations[index],
                weather: data
            }));
        } catch (error) {
            console.error('Error fetching multi-location weather:', error);
            return [];
        }
    }

    /**
     * Get aggregated risk score
     */
    async getAggregatedRiskScore(latitude, longitude) {
        try {
            const [weather, historical] = await Promise.all([
                this.getWeatherData(latitude, longitude),
                this.getHistoricalData(
                    latitude, 
                    longitude,
                    this.getDateString(30),
                    this.getDateString(0)
                )
            ]);
            
            // Calculate risk score based on multiple factors
            let riskScore = 50; // Base score
            
            if (weather) {
                const temp = weather.current?.temperature_2m || 20;
                const precipitation = weather.current?.precipitation || 0;
                const windSpeed = weather.current?.wind_speed_10m || 0;
                
                // Temperature risk
                if (temp > 35) riskScore += 20;
                else if (temp > 30) riskScore += 10;
                else if (temp < 0) riskScore += 15;
                
                // Precipitation risk
                if (precipitation > 50) riskScore += 15;
                else if (precipitation > 25) riskScore += 8;
                
                // Wind risk
                if (windSpeed > 20) riskScore += 15;
                else if (windSpeed > 15) riskScore += 8;
            }
            
            // Normalize score to 0-100
            riskScore = Math.min(100, Math.max(0, riskScore));
            
            return {
                score: riskScore,
                level: this.getRiskLevel(riskScore),
                factors: {
                    weather: weather,
                    historical: historical
                }
            };
        } catch (error) {
            console.error('Error calculating risk score:', error);
            return {
                score: 50,
                level: 'medium',
                error: true
            };
        }
    }

    /**
     * Stream real-time data updates
     */
    streamRealtimeData(callback, interval = 5000) {
        const streamId = setInterval(async () => {
            const data = await this.getRandomizedData();
            callback(data);
        }, interval);
        
        return {
            stop: () => clearInterval(streamId)
        };
    }

    /**
     * Get randomized data for demo purposes
     */
    async getRandomizedData() {
        return {
            timestamp: new Date().toISOString(),
            metrics: {
                riskIndex: 70 + Math.random() * 10,
                temperature: 1.5 + Math.random() * 0.5,
                co2Level: 420 + Math.random() * 5,
                events: Math.floor(150 + Math.random() * 20),
                resilience: 85 + Math.random() * 5
            },
            alerts: this.generateRandomAlerts()
        };
    }

    /**
     * Generate random alerts
     */
    generateRandomAlerts() {
        const alertTypes = [
            { type: 'heatwave', message: 'Heat wave detected', severity: 'high' },
            { type: 'flooding', message: 'Flooding risk increased', severity: 'medium' },
            { type: 'drought', message: 'Drought conditions worsening', severity: 'high' },
            { type: 'storm', message: 'Storm system developing', severity: 'low' },
            { type: 'wildfire', message: 'Wildfire risk elevated', severity: 'medium' }
        ];
        
        const alerts = [];
        const count = Math.floor(Math.random() * 3);
        
        for (let i = 0; i < count; i++) {
            const alert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
            alerts.push({
                ...alert,
                id: Date.now() + i,
                timestamp: new Date().toISOString(),
                location: this.getRandomLocation()
            });
        }
        
        return alerts;
    }

    /**
     * Get random location
     */
    getRandomLocation() {
        const locations = [
            'North America',
            'Europe',
            'Asia',
            'South America',
            'Africa',
            'Australia',
            'Antarctica'
        ];
        return locations[Math.floor(Math.random() * locations.length)];
    }

    /**
     * Helper: Get risk level from score
     */
    getRiskLevel(score) {
        if (score >= 80) return 'critical';
        if (score >= 60) return 'high';
        if (score >= 40) return 'medium';
        if (score >= 20) return 'low';
        return 'minimal';
    }

    /**
     * Helper: Get date string for API
     */
    getDateString(daysOffset) {
        const date = new Date();
        date.setDate(date.getDate() - daysOffset);
        return date.toISOString().split('T')[0];
    }

    /**
     * Cache management
     */
    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    isCacheValid(key) {
        if (!this.cache.has(key)) return false;
        
        const cached = this.cache.get(key);
        const age = Date.now() - cached.timestamp;
        
        if (age > this.cacheTimeout) {
            this.cache.delete(key);
            return false;
        }
        
        return true;
    }

    clearCache() {
        this.cache.clear();
    }

    /**
     * Export data to CSV
     */
    exportToCSV(data, filename = 'climate_data.csv') {
        const csv = this.convertToCSV(data);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * Convert data to CSV format
     */
    convertToCSV(data) {
        if (!Array.isArray(data) || data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const rows = data.map(row => 
            headers.map(header => {
                const value = row[header];
                return typeof value === 'object' ? JSON.stringify(value) : value;
            }).join(',')
        );
        
        return [headers.join(','), ...rows].join('\n');
    }
}

// Create singleton instance
const apiService = new APIService();

// Export for use in other modules
window.APIService = APIService;
window.apiService = apiService;