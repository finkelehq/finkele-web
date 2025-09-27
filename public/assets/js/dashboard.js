/**
 * Finkele Climate Dashboard Module
 * Real-time climate data visualization
 */

class ClimateRiskDashboard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.updateInterval = 5000; // 5 seconds
        this.data = {
            riskIndex: 73.2,
            temperature: 1.8,
            co2Level: 421,
            events: 156,
            resilience: 87
        };
        
        this.init();
    }
    
    init() {
        this.render();
        this.startLiveUpdates();
        this.initCharts();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="dashboard-full">
                <div class="dashboard-header">
                    <h2>Climate Risk Intelligence Dashboard</h2>
                    <div class="live-status">
                        <span class="live-dot"></span>
                        <span>LIVE MONITORING</span>
                        <span id="current-time">${this.getCurrentTime()}</span>
                    </div>
                </div>
                
                <div class="metrics-row">
                    ${this.renderMetrics()}
                </div>
                
                <div class="charts-row">
                    <div class="chart-container">
                        <canvas id="risk-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="trend-chart"></canvas>
                    </div>
                </div>
                
                <div class="activity-feed">
                    <h3>Recent Climate Events</h3>
                    <div id="activity-list"></div>
                </div>
            </div>
        `;
    }
    
    renderMetrics() {
        const metrics = [
            { label: 'Risk Index', value: this.data.riskIndex, unit: '', trend: 'down' },
            { label: 'Temperature', value: `+${this.data.temperature}`, unit: '°C', trend: 'up' },
            { label: 'CO₂ Level', value: this.data.co2Level, unit: 'ppm', trend: 'up' },
            { label: 'Events', value: this.data.events, unit: '', trend: 'up' },
            { label: 'Resilience', value: this.data.resilience, unit: '%', trend: 'up' }
        ];
        
        return metrics.map(metric => `
            <div class="metric-card">
                <div class="metric-label">${metric.label}</div>
                <div class="metric-value">${metric.value}${metric.unit}</div>
                <div class="metric-trend ${metric.trend}">
                    ${metric.trend === 'up' ? '↑' : '↓'}
                </div>
            </div>
        `).join('');
    }
    
    startLiveUpdates() {
        // Update time every second
        setInterval(() => {
            const timeElement = document.getElementById('current-time');
            if (timeElement) {
                timeElement.textContent = this.getCurrentTime();
            }
        }, 1000);
        
        // Update data every 5 seconds
        setInterval(() => {
            this.updateData();
            this.updateActivity();
        }, this.updateInterval);
    }
    
    updateData() {
        // Simulate data changes
        this.data.riskIndex += (Math.random() - 0.5) * 2;
        this.data.temperature += (Math.random() - 0.5) * 0.1;
        this.data.co2Level += (Math.random() - 0.3) * 0.5;
        this.data.events += Math.floor(Math.random() * 3);
        this.data.resilience += (Math.random() - 0.5) * 1;
        
        // Update display
        this.render();
    }
    
    updateActivity() {
        const activities = [
            'Heatwave detected in Southern Europe',
            'Sea level rise alert - Pacific Islands',
            'Wildfire risk increasing - Western US',
            'Cyclone formation - Indian Ocean',
            'Drought conditions - Sub-Saharan Africa'
        ];
        
        const activity = activities[Math.floor(Math.random() * activities.length)];
        const activityList = document.getElementById('activity-list');
        
        if (activityList) {
            const newItem = document.createElement('div');
            newItem.className = 'activity-item';
            newItem.innerHTML = `
                <span class="activity-time">${this.getCurrentTime()}</span>
                <span class="activity-text">${activity}</span>
            `;
            
            activityList.insertBefore(newItem, activityList.firstChild);
            
            // Keep only last 5 items
            while (activityList.children.length > 5) {
                activityList.removeChild(activityList.lastChild);
            }
        }
    }
    
    initCharts() {
        // Initialize Chart.js or other charting library
        // This is a placeholder for chart initialization
        console.log('Charts initialized');
    }
    
    getCurrentTime() {
        return new Date().toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Initialize dashboard if container exists
document.addEventListener('DOMContentLoaded', () => {
    const dashboardContainer = document.getElementById('dashboard-container');
    if (dashboardContainer) {
        new ClimateRiskDashboard('dashboard-container');
    }
});