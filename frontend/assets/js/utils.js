/**
 * FedBrrrr Utility Functions
 */

const Utils = {
    /**
     * Format a number with appropriate decimal places and thousands separators
     */
    formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) {
            return '-';
        }
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },

    /**
     * Format a value with its unit
     */
    formatValue(value, unit) {
        const formatted = this.formatNumber(value);
        if (!unit) return formatted;

        if (unit === '%' || unit === '% YoY' || unit === '% of income' || unit === '% differential') {
            return `${formatted}${unit.startsWith('%') ? '%' : ' ' + unit}`;
        }
        return `${formatted} ${unit}`;
    },

    /**
     * Format a date string for display
     */
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    /**
     * Get status color class
     */
    getStatusClass(status) {
        const classes = {
            green: 'text-success',
            yellow: 'text-warning',
            red: 'text-error'
        };
        return classes[status] || 'text-base-content';
    },

    /**
     * Get status label
     */
    getStatusLabel(status) {
        const labels = {
            green: 'Healthy',
            yellow: 'Caution',
            red: 'Warning'
        };
        return labels[status] || 'Unknown';
    },

    /**
     * Get trend icon
     */
    getTrendIcon(trend) {
        const icons = {
            improving: '↑',
            deteriorating: '↓',
            stable: '→'
        };
        return icons[trend] || '→';
    },

    /**
     * Get trend class
     */
    getTrendClass(trend) {
        const classes = {
            improving: 'trend-improving',
            deteriorating: 'trend-deteriorating',
            stable: 'trend-stable'
        };
        return classes[trend] || 'trend-stable';
    },

    /**
     * Get trend label
     */
    getTrendLabel(trend) {
        const labels = {
            improving: 'Improving',
            deteriorating: 'Deteriorating',
            stable: 'Stable'
        };
        return labels[trend] || 'Stable';
    },

    /**
     * Fetch JSON data from a URL
     */
    async fetchJSON(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${url}:`, error);
            throw error;
        }
    },

    /**
     * Debounce function for performance
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Get color for chart based on status
     */
    getChartColor(status, alpha = 1) {
        const colors = {
            green: `rgba(34, 197, 94, ${alpha})`,   // Tailwind green-500
            yellow: `rgba(234, 179, 8, ${alpha})`,   // Tailwind yellow-500
            red: `rgba(239, 68, 68, ${alpha})`       // Tailwind red-500
        };
        return colors[status] || `rgba(148, 163, 184, ${alpha})`; // Slate-400 default
    },

    /**
     * Generate gradient for sparkline based on data trend
     */
    getSparklineGradient(ctx, status) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 50);
        const color = this.getChartColor(status);
        gradient.addColorStop(0, color.replace(/[\d.]+\)$/, '0.3)'));
        gradient.addColorStop(1, color.replace(/[\d.]+\)$/, '0.05)'));
        return gradient;
    }
};

// Make available globally
window.Utils = Utils;
