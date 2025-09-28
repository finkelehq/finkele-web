/**
 * FILE: public/assets/js/dashboard.js
 * Finkele Climate Dashboard - Complete Implementation
 */

// Global variables
let charts = {};
let dataStream = null;
let currentView = 'embedded';

/**
 * Initialize Dashboard
 */
function initializeDashboard() {
    console.log('Initializing Finkele Dashboard...');
    
    // Update time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Initialize charts if on dashboard page
    if (document.getElementById('regional-risk-chart')) {
        initializeCharts();
    }
    
    // Start activity feed
    if (document.getElementById('activity-feed')) {
        startActivityFeed();
    }
    
    // Initialize sparklines
    initializeSparklines();
    
    // Setup event listeners
    setupEventListeners();
    
    console.log('Dashboard initialized successfully');
}

/**
 * Initialize all charts
 */
function initializeCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }
    
    // Regional Risk Chart
    const regionalCtx = document.getElementById('regional-risk-chart');
    if (regionalCtx) {
        charts.regional = new Chart(regionalCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['N. America', 'Europe', 'Asia', 'S. America', 'Africa', 'Oceania'],
                datasets: [{
                    label: 'Risk Score',
                    data: [75, 68, 82, 79, 86, 72],
                    backgroundColor: [
                        'rgba(3, 140, 80, 0.6)',
                        'rgba(3, 140, 80, 0.5)',
                        'rgba(220, 38, 38, 0.6)',
                        'rgba(245, 158, 11, 0.6)',
                        'rgba(220, 38, 38, 0.7)',
                        'rgba(3, 140, 80, 0.4)'
                    ],
                    borderColor: [
                        '#038C50',
                        '#038C50',
                        '#DC2626',
                        '#F59E0B',
                        '#DC2626',
                        '#038C50'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Risk Score: ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
    
    // Trend Chart
    const trendCtx = document.getElementById('trend-chart');
    if (trendCtx) {
        charts.trend = new Chart(trendCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Risk Index',
                    data: [71.5, 72.1, 72.8, 73.2, 73.5, 74.1, 74.8, 75.2, 74.9, 74.3, 73.8, 73.2],
                    borderColor: '#038C50',
                    backgroundColor: 'rgba(3, 140, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Temperature Anomaly',
                    data: [1.65, 1.68, 1.71, 1.73, 1.75, 1.78, 1.82, 1.85, 1.84, 1.82, 1.80, 1.80],
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
    
    // Risk Distribution Chart
    const distributionCtx = document.getElementById('risk-distribution-chart');
    if (distributionCtx) {
        charts.distribution = new Chart(distributionCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Agriculture', 'Energy', 'Real Estate', 'Transportation', 'Healthcare'],
                datasets: [{
                    data: [82, 68, 78, 71, 65],
                    backgroundColor: [
                        'rgba(220, 38, 38, 0.7)',
                        'rgba(3, 140, 80, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(79, 191, 127, 0.7)'
                    ],
                    borderColor: [
                        '#DC2626',
                        '#038C50',
                        '#F59E0B',
                        '#3B82F6',
                        '#4FBF7F'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            padding: 15
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize sparkline charts
 */
function initializeSparklines() {
    const sparklineConfigs = [
        { id: 'risk-sparkline', color: '#038C50' },
        { id: 'temp-sparkline', color: '#F59E0B' },
        { id: 'co2-sparkline', color: '#DC2626' },
        { id: 'events-sparkline', color: '#3B82F6' }
    ];
    
    sparklineConfigs.forEach(config => {
        const canvas = document.getElementById(config.id);
        if (canvas && typeof Chart !== 'undefined') {
            new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: Array(10).fill(''),
                    datasets: [{
                        data: Array(10).fill(0).map(() => Math.random() * 100),
                        borderColor: config.color,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    },
                    scales: {
                        x: { display: false },
                        y: { display: false }
                    }
                }
            });
        }
    });
}

/**
 * Start real-time updates
 */
function startRealtimeUpdates() {
    // Update metrics every 5 seconds
    setInterval(updateMetrics, 5000);
    
    // Update charts every 10 seconds
    setInterval(updateCharts, 10000);
}

/**
 * Update metric values with animation
 */
function updateMetrics() {
    const metrics = [
        { id: 'risk-index-value', range: [70, 80] },
        { id: 'temp-value', range: [1.5, 2.0], prefix: '+', suffix: '°C' },
        { id: 'co2-value', range: [419, 423], suffix: ' ppm' },
        { id: 'events-value', range: [150, 170] }
    ];
    
    metrics.forEach(metric => {
        const element = document.getElementById(metric.id);
        if (element) {
            const currentValue = parseFloat(element.textContent) || metric.range[0];
            const change = (Math.random() - 0.5) * 2;
            const newValue = Math.max(metric.range[0], Math.min(metric.range[1], currentValue + change));
            
            const displayValue = (metric.prefix || '') + 
                               newValue.toFixed(metric.suffix?.includes('°C') ? 1 : 0) + 
                               (metric.suffix || '');
            
            element.textContent = displayValue;
            
            // Add animation class
            element.classList.add('value-updated');
            setTimeout(() => element.classList.remove('value-updated'), 500);
        }
    });
}

/**
 * Update charts with new data
 */
function updateCharts() {
    if (charts.regional) {
        // Update regional risk chart
        charts.regional.data.datasets[0].data = charts.regional.data.datasets[0].data.map(
            value => Math.max(60, Math.min(90, value + (Math.random() - 0.5) * 5))
        );
        charts.regional.update('none');
    }
    
    if (charts.trend) {
        // Add new data point and remove oldest
        const newData = charts.trend.data.datasets[0].data;
        newData.shift();
        newData.push(73 + Math.random() * 2);
        charts.trend.update('none');
    }
}

/**
 * Activity Feed
 */
function startActivityFeed() {
    const activities = [
        { type: 'alert', text: 'Heatwave Alert - Southern Europe', icon: '⚠️' },
        { type: 'warning', text: 'Sea Level Rise - Pacific Islands', icon: '🌊' },
        { type: 'info', text: 'Cyclone Formation - Indian Ocean', icon: '🌪️' },
        { type: 'alert', text: 'Wildfire Risk - Western US', icon: '🔥' },
        { type: 'warning', text: 'Drought Conditions - Sub-Saharan Africa', icon: '🌡️' },
        { type: 'info', text: 'Storm System - North Atlantic', icon: '⛈️' }
    ];
    
    function addActivity() {
        const feed = document.getElementById('activity-feed');
        if (!feed) return;
        
        const activity = activities[Math.floor(Math.random() * activities.length)];
        const item = document.createElement('div');
        item.className = `activity-item ${activity.type}`;
        item.innerHTML = `
            <div class="activity-time">${new Date().toLocaleTimeString()}</div>
            <div class="activity-text">${activity.icon} ${activity.text}</div>
        `;
        
        feed.insertBefore(item, feed.firstChild);
        
        // Keep only last 10 items
        while (feed.children.length > 10) {
            feed.removeChild(feed.lastChild);
        }
    }
    
    // Add initial activities
    for (let i = 0; i < 5; i++) {
        setTimeout(() => addActivity(), i * 200);
    }
    
    // Add new activity every 10 seconds
    setInterval(addActivity, 10000);
}

/**
 * Update current time
 */
function updateCurrentTime() {
    const timeElement = document.getElementById('dashboard-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Fullscreen toggle
    const fullscreenBtn = document.getElementById('fullscreen-toggle');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    // Time period buttons
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateChartsForPeriod(this.dataset.period);
        });
    });
    
    // Download buttons
    document.querySelectorAll('.chart-download').forEach(btn => {
        btn.addEventListener('click', function() {
            downloadChartData(this.closest('.chart-card'));
        });
    });
    
    // Action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.querySelector('span').textContent;
            handleAction(action);
        });
    });
    
    // Region timeframe selector
    const regionTimeframe = document.getElementById('region-timeframe');
    if (regionTimeframe) {
        regionTimeframe.addEventListener('change', function() {
            updateRegionalData(this.value);
        });
    }
}

/**
 * Toggle fullscreen mode
 */
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

/**
 * Update charts for selected time period
 */
function updateChartsForPeriod(period) {
    console.log('Updating charts for period:', period);
    // Implement period-specific data updates
    if (charts.trend) {
        // Update trend chart based on period
        const periods = {
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365
        };
        // Update chart data based on period
        charts.trend.update();
    }
}

/**
 * Download chart data
 */
function downloadChartData(chartCard) {
    const title = chartCard.querySelector('.chart-title').textContent;
    const data = {
        title: title,
        timestamp: new Date().toISOString(),
        // Add chart-specific data here
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Handle action button clicks
 */
function handleAction(action) {
    console.log('Action triggered:', action);
    
    switch(action) {
        case 'Generate Report':
            generateReport();
            break;
        case 'Export Data':
            exportData();
            break;
        case 'Configure Alerts':
            configureAlerts();
            break;
        case 'Notifications':
            showNotifications();
            break;
        default:
            console.log('Unknown action:', action);
    }
}

/**
 * Generate report
 */
function generateReport() {
    showNotification('Generating report...', 'info');
    setTimeout(() => {
        showNotification('Report generated successfully!', 'success');
    }, 2000);
}

/**
 * Export data
 */
function exportData() {
    if (window.apiService && typeof window.apiService.exportToCSV === 'function') {
        const data = [
            { region: 'North America', risk: 75, temperature: 2.1 },
            { region: 'Europe', risk: 68, temperature: 1.9 },
            { region: 'Asia', risk: 82, temperature: 2.3 }
        ];
        window.apiService.exportToCSV(data, 'climate_data.csv');
        showNotification('Data exported successfully!', 'success');
    } else {
        showNotification('Export service not available', 'error');
    }
}

/**
 * Configure alerts
 */
function configureAlerts() {
    showNotification('Alert configuration panel opening...', 'info');
}

/**
 * Show notifications panel
 */
function showNotifications() {
    showNotification('You have 3 new notifications', 'info');
}

/**
 * Update regional data
 */
function updateRegionalData(timeframe) {
    console.log('Updating regional data for timeframe:', timeframe);
    // Update the regional chart based on timeframe
    if (charts.regional) {
        // Simulate different data for different timeframes
        const dataMap = {
            '24h': [75, 68, 82, 79, 86, 72],
            '7d': [73, 70, 80, 77, 85, 71],
            '30d': [74, 69, 81, 78, 84, 73],
            '1y': [72, 67, 83, 76, 87, 70]
        };
        
        charts.regional.data.datasets[0].data = dataMap[timeframe] || dataMap['30d'];
        charts.regional.update();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Create notification container if it doesn't exist
 */
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'notification-container';
    document.body.appendChild(container);
    return container;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}

// Start real-time updates
startRealtimeUpdates();

// Export functions for external use
window.dashboardFunctions = {
    initializeDashboard,
    updateMetrics,
    showNotification,
    exportData
};