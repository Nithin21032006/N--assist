// N-Assist Analytics Engine

document.addEventListener("DOMContentLoaded", () => {
    loadAnalytics();
});

let charts = {};

async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics/data');
        const data = await res.json();
        
        // Populate text metrics
        document.getElementById('metricTotal').innerText = data.total_tasks;
        document.getElementById('metricPending').innerText = data.pending_tasks;
        document.getElementById('metricCompleted').innerText = data.completed_tasks;
        document.getElementById('metricRate').innerText = data.completion_rate + '%';
        
        // Render charts
        renderRatioChart(data.completed_tasks, data.pending_tasks);
        renderTimelineChart(data.monthly_data);
        renderCategoryChart(data.category_data);
        renderWeeklyChart(data.weekly_activity);
        
    } catch (err) {
        console.error("Error loading analytics data:", err);
        showToast("Failed to compile productivity metrics.", "error");
    }
}

// Global configuration helper to match light/dark styling
function getChartThemeColors() {
    const isLight = document.body.classList.contains("light-theme");
    return {
        text: isLight ? "#475569" : "#94a3b8",
        grid: isLight ? "rgba(15, 23, 42, 0.05)" : "rgba(255, 255, 255, 0.05)",
        panelBg: isLight ? "#ffffff" : "#07080a",
        purpleGradient: ['#00ffd0', '#00b0ff'],
        emeraldGradient: ['#00ff9f', '#00c853'],
    };
}

function renderRatioChart(completed, pending) {
    const ctx = document.getElementById("ratioChart").getContext("2d");
    if (charts.ratio) charts.ratio.destroy();
    
    const colors = getChartThemeColors();
    
    // Fallback if 0 tasks
    const dataValues = (completed === 0 && pending === 0) ? [0, 1] : [completed, pending];
    const borderCol = (completed === 0 && pending === 0) ? 'rgba(255,255,255,0.05)' : '#10b981';
    
    charts.ratio = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Pending'],
            datasets: [{
                data: dataValues,
                backgroundColor: [
                    '#10b981',
                    'rgba(255, 255, 255, 0.04)'
                ],
                borderColor: [
                    '#059669',
                    'rgba(255, 255, 255, 0.05)'
                ],
                borderWidth: 1.5,
                cutout: '75%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.text,
                        font: { family: 'Outfit', size: 12 }
                    }
                }
            }
        }
    });
}

function renderTimelineChart(monthlyData) {
    const ctx = document.getElementById("timelineChart").getContext("2d");
    if (charts.timeline) charts.timeline.destroy();
    
    const colors = getChartThemeColors();
    
    // Create background gradient for line area
    const areaGlow = ctx.createLinearGradient(0, 0, 0, 300);
    areaGlow.addColorStop(0, 'rgba(0, 242, 254, 0.15)');
    areaGlow.addColorStop(1, 'rgba(0, 114, 255, 0)');

    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Tasks Completed',
                data: monthlyData,
                borderColor: '#00f2fe',
                borderWidth: 3,
                backgroundColor: areaGlow,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#00ffd0',
                pointBorderColor: '#07080a',
                pointHoverRadius: 6,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { family: 'Outfit' } }
                },
                y: {
                    grid: { color: colors.grid },
                    ticks: { stepSize: 1, color: colors.text, font: { family: 'Outfit' } }
                }
            }
        }
    });
}

function renderCategoryChart(categoryMap) {
    const ctx = document.getElementById("categoryChart").getContext("2d");
    if (charts.category) charts.category.destroy();
    
    const colors = getChartThemeColors();
    const labels = Object.keys(categoryMap);
    const dataValues = Object.values(categoryMap);
    
    charts.category = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Task Volume',
                data: dataValues,
                backgroundColor: 'rgba(0, 242, 254, 0.08)',
                borderColor: '#00b0ff',
                borderWidth: 2,
                pointBackgroundColor: '#00ffd0',
                pointBorderColor: '#07080a',
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                r: {
                    grid: { color: colors.grid },
                    angleLines: { color: colors.grid },
                    pointLabels: {
                        color: colors.text,
                        font: { family: 'Outfit', size: 11, weight: 'bold' }
                    },
                    ticks: {
                        stepSize: 1,
                        backdropColor: 'transparent',
                        color: colors.text
                    }
                }
            }
        }
    });
}

function renderWeeklyChart(weeklyData) {
    const ctx = document.getElementById("weeklyChart").getContext("2d");
    if (charts.weekly) charts.weekly.destroy();
    
    const colors = getChartThemeColors();
    
    // Custom gradient for bars
    const barGradient = ctx.createLinearGradient(0, 0, 0, 300);
    barGradient.addColorStop(0, '#4facfe');
    barGradient.addColorStop(1, '#00ffd0');

    charts.weekly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Deadlines Handled',
                data: weeklyData,
                backgroundColor: barGradient,
                borderRadius: 4,
                maxBarThickness: 32
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { family: 'Outfit' } }
                },
                y: {
                    grid: { color: colors.grid },
                    ticks: { stepSize: 1, color: colors.text, font: { family: 'Outfit' } }
                }
            }
        }
    });
}

// Re-render charts on theme change to update colors correctly
document.getElementById("themeToggleBtn")?.addEventListener("click", () => {
    // Small delay to let body class update first
    setTimeout(() => {
        loadAnalytics();
    }, 50);
});
