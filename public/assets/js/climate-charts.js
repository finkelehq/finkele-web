// Climate Analytics Charts for Finkele
// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeClimateCharts();
});

function initializeClimateCharts() {
    // Temperature Trend Chart
    const tempCtx = document.getElementById('temperatureChart');
    if (tempCtx) {
        const temperatureChart = new Chart(tempCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Global Temperature Anomaly (°C)',
                    data: [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.8, 1.7, 1.6, 1.5, 1.4],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Historical Average',
                    data: [0.8, 0.8, 0.9, 0.9, 1.0, 1.0, 1.1, 1.1, 1.0, 0.9, 0.9, 0.8],
                    borderColor: 'rgb(150, 150, 150)',
                    backgroundColor: 'rgba(150, 150, 150, 0.05)',
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Temperature Trends',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Temperature Anomaly (°C)'
                        }
                    }
                }
            }
        });
    }

    // CO2 Levels Chart
    const co2Ctx = document.getElementById('co2Chart');
    if (co2Ctx) {
        const co2Chart = new Chart(co2Ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['2019', '2020', '2021', '2022', '2023', '2024', '2025'],
                datasets: [{
                    label: 'CO₂ Concentration (ppm)',
                    data: [410, 412, 415, 417, 419, 420, 421],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 99, 132, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'CO₂ Concentration Levels',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 400,
                        title: {
                            display: true,
                            text: 'CO₂ (ppm)'
                        }
                    }
                }
            }
        });
    }

    // Precipitation Chart
    const precipCtx = document.getElementById('precipitationChart');
    if (precipCtx) {
        const precipitationChart = new Chart(precipCtx.getContext('2d'), {
            type: 'radar',
            data: {
                labels: ['North America', 'Europe', 'Asia', 'Africa', 'South America', 'Oceania'],
                datasets: [{
                    label: 'Current Risk Level',
                    data: [65, 75, 85, 70, 60, 55],
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    pointBackgroundColor: 'rgb(255, 159, 64)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 159, 64)'
                }, {
                    label: 'Projected 2030',
                    data: [75, 85, 95, 80, 70, 65],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    pointBackgroundColor: 'rgb(255, 99, 132)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 99, 132)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Regional Climate Risk Assessment',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    }

    // Risk Assessment Doughnut Chart
    const riskCtx = document.getElementById('riskChart');
    if (riskCtx) {
        const riskChart = new Chart(riskCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Critical Risk', 'High Risk', 'Medium Risk', 'Low Risk', 'Minimal Risk'],
                datasets: [{
                    data: [12, 23, 35, 20, 10],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(54, 162, 235, 0.8)'
                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Global Assets Risk Distribution',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Animate the stats numbers
    animateStats();
}

// Animate the statistics numbers
function animateStats() {
    const stats = [
        { selector: '.stat-number', target: 73.2, suffix: '', decimals: 1 },
        { selector: '.temp-value', target: 1.8, suffix: '°C', decimals: 1, prefix: '+' },
        { selector: '.co2-value', target: 421, suffix: ' ppm', decimals: 0 },
        { selector: '.risk-value', target: 87, suffix: '%', decimals: 0 }
    ];

    stats.forEach(stat => {
        const element = document.querySelector(stat.selector);
        if (element) {
            animateValue(element, 0, stat.target, 2000, stat);
        }
    });
}

function animateValue(element, start, end, duration, options) {
    const startTime = performance.now();
    const prefix = options.prefix || '';
    const suffix = options.suffix || '';
    const decimals = options.decimals || 0;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = start + (end - start) * easeOutQuart;
        
        element.textContent = prefix + current.toFixed(decimals) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Update data periodically (simulate real-time updates)
setInterval(() => {
    // Update the "LIVE" indicator
    const liveIndicator = document.querySelector('.live-indicator');
    if (liveIndicator) {
        liveIndicator.style.opacity = '0';
        setTimeout(() => {
            liveIndicator.style.opacity = '1';
        }, 500);
    }
    
    // You can add code here to fetch real data from your API
    // fetchLatestClimateData();
}, 30000); // Update every 30 seconds