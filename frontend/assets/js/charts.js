/**
 * FedBrrrr Chart Functions
 */

const Charts = {
    // Store chart instances for cleanup
    sparklineCharts: new Map(),
    detailChart: null,

    /**
     * Create a sparkline chart
     */
    createSparkline(canvasId, data, status) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (this.sparklineCharts.has(canvasId)) {
            this.sparklineCharts.get(canvasId).destroy();
        }

        const values = data.map(d => d.value);
        const labels = data.map(d => d.date);
        const color = Utils.getChartColor(status);

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    borderColor: color,
                    backgroundColor: Utils.getSparklineGradient(ctx, status),
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 0
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
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 500
                }
            }
        });

        this.sparklineCharts.set(canvasId, chart);
        return chart;
    },

    /**
     * Create the detail chart in the modal
     */
    createDetailChart(data, indicator) {
        const canvas = document.getElementById('detail-chart');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart
        if (this.detailChart) {
            this.detailChart.destroy();
        }

        const values = data.map(d => d.value);
        const labels = data.map(d => d.date);
        const color = Utils.getChartColor(indicator.status);

        // Calculate threshold lines if available
        const annotations = this.createThresholdAnnotations(indicator.thresholds);

        this.detailChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: indicator.name,
                    data: values,
                    borderColor: color,
                    backgroundColor: color.replace(/[\d.]+\)$/, '0.1)'),
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    pointHoverBackgroundColor: color
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: (items) => Utils.formatDate(items[0].label),
                            label: (item) => `${indicator.name}: ${Utils.formatValue(item.raw, indicator.unit)}`
                        }
                    },
                    annotation: annotations.length > 0 ? { annotations } : undefined
                },
                scales: {
                    x: {
                        display: true,
                        grid: { display: false },
                        ticks: {
                            maxTicksLimit: 8,
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                return new Date(label).toLocaleDateString('en-US', {
                                    year: '2-digit',
                                    month: 'short'
                                });
                            }
                        }
                    },
                    y: {
                        display: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: {
                            callback: (value) => Utils.formatNumber(value, 1)
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 750
                }
            }
        });

        return this.detailChart;
    },

    /**
     * Create threshold annotation lines for the detail chart
     */
    createThresholdAnnotations(thresholds) {
        if (!thresholds) return [];

        const annotations = [];

        // Green threshold line
        if (thresholds.green_max !== null) {
            annotations.push({
                type: 'line',
                yMin: thresholds.green_max,
                yMax: thresholds.green_max,
                borderColor: 'rgba(34, 197, 94, 0.5)',
                borderWidth: 1,
                borderDash: [5, 5],
                label: {
                    display: true,
                    content: 'Green threshold',
                    position: 'end'
                }
            });
        }

        if (thresholds.green_min !== null) {
            annotations.push({
                type: 'line',
                yMin: thresholds.green_min,
                yMax: thresholds.green_min,
                borderColor: 'rgba(34, 197, 94, 0.5)',
                borderWidth: 1,
                borderDash: [5, 5]
            });
        }

        // Red threshold line
        if (thresholds.red_min !== null) {
            annotations.push({
                type: 'line',
                yMin: thresholds.red_min,
                yMax: thresholds.red_min,
                borderColor: 'rgba(239, 68, 68, 0.5)',
                borderWidth: 1,
                borderDash: [5, 5]
            });
        }

        if (thresholds.red_max !== null) {
            annotations.push({
                type: 'line',
                yMin: thresholds.red_max,
                yMax: thresholds.red_max,
                borderColor: 'rgba(239, 68, 68, 0.5)',
                borderWidth: 1,
                borderDash: [5, 5]
            });
        }

        return annotations;
    },

    /**
     * Cleanup all charts
     */
    destroyAll() {
        this.sparklineCharts.forEach(chart => chart.destroy());
        this.sparklineCharts.clear();

        if (this.detailChart) {
            this.detailChart.destroy();
            this.detailChart = null;
        }
    }
};

// Make available globally
window.Charts = Charts;
