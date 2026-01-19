/**
 * FedBrrrr Main Application
 */

const App = {
    // Data storage
    data: null,
    currentIndicator: null,

    /**
     * Initialize the application
     */
    async init() {
        console.log('FedBrrrr initializing...');

        // Setup theme toggle
        this.setupThemeToggle();

        // Load data
        await this.loadData();

        // Setup modal handlers
        this.setupModal();

        console.log('FedBrrrr initialized');
    },

    /**
     * Setup theme toggle functionality
     */
    setupThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        const html = document.documentElement;

        // Check for saved preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            html.setAttribute('data-theme', savedTheme);
            toggle.checked = savedTheme === 'light';
        }

        toggle.addEventListener('change', () => {
            const theme = toggle.checked ? 'light' : 'dark';
            html.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        });
    },

    /**
     * Load indicator data from JSON
     */
    async loadData() {
        try {
            this.data = await Utils.fetchJSON('data/indicators.json');

            // Update last updated timestamp
            document.getElementById('last-updated').textContent =
                Utils.formatDate(this.data.generated_at);

            // Render indicators
            this.renderIndicators('economy', this.data.economy);
            this.renderIndicators('household', this.data.household);

        } catch (error) {
            console.error('Failed to load data:', error);
            this.showError('economy-indicators', 'Failed to load economy indicators');
            this.showError('household-indicators', 'Failed to load household indicators');
        }
    },

    /**
     * Show error message in a container
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="alert alert-error col-span-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>${message}</span>
            </div>
        `;
    },

    /**
     * Render indicator cards
     */
    renderIndicators(category, indicators) {
        const containerId = `${category}-indicators`;
        const container = document.getElementById(containerId);

        if (!indicators || indicators.length === 0) {
            container.innerHTML = `
                <div class="alert col-span-full">
                    <span>No ${category} indicators available</span>
                </div>
            `;
            return;
        }

        container.innerHTML = indicators.map(indicator => this.createCard(indicator, category)).join('');

        // Create sparklines after cards are rendered
        indicators.forEach(indicator => {
            if (indicator.sparkline && indicator.sparkline.length > 0) {
                Charts.createSparkline(
                    `sparkline-${indicator.id}`,
                    indicator.sparkline,
                    indicator.status
                );
            }
        });

        // Add click handlers
        indicators.forEach(indicator => {
            const card = document.getElementById(`card-${indicator.id}`);
            if (card) {
                card.addEventListener('click', () => this.openModal(indicator, category));
            }
        });
    },

    /**
     * Create an indicator card HTML
     */
    createCard(indicator, category) {
        const statusClass = Utils.getStatusClass(indicator.status);
        const trendClass = Utils.getTrendClass(indicator.trend);
        const trendIcon = Utils.getTrendIcon(indicator.trend);

        const changePrefix = indicator.change_value >= 0 ? '+' : '';
        const changeDisplay = `${changePrefix}${Utils.formatNumber(indicator.change_value)}`;

        return `
            <div id="card-${indicator.id}"
                 class="card bg-base-100 shadow-lg indicator-card cursor-pointer hover:bg-base-200 transition-colors">
                <div class="card-body p-4">
                    <div class="flex items-start justify-between">
                        <h3 class="card-title text-base">${indicator.name}</h3>
                        <div class="status-indicator ${indicator.status}" title="${Utils.getStatusLabel(indicator.status)}"></div>
                    </div>

                    <div class="mt-2">
                        <div class="card-value ${statusClass}">
                            ${Utils.formatNumber(indicator.current_value)}
                            <span class="card-unit">${indicator.unit}</span>
                        </div>
                        <div class="text-sm text-base-content/60 mt-1">
                            <span class="${trendClass}">${trendIcon} ${changeDisplay}</span>
                            <span class="ml-2">${Utils.formatDate(indicator.current_date)}</span>
                        </div>
                    </div>

                    <div class="sparkline-container mt-3">
                        <canvas id="sparkline-${indicator.id}"></canvas>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Setup modal handlers
     */
    setupModal() {
        const modal = document.getElementById('detail-modal');

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.open) {
                modal.close();
            }
        });

        // Cleanup chart when modal closes
        modal.addEventListener('close', () => {
            this.currentIndicator = null;
        });
    },

    /**
     * Open the detail modal for an indicator
     */
    async openModal(indicator, category) {
        this.currentIndicator = indicator;

        const modal = document.getElementById('detail-modal');

        // Update modal content
        document.getElementById('modal-title').textContent = indicator.name;
        document.getElementById('modal-description').textContent = indicator.description;
        document.getElementById('modal-value').textContent =
            Utils.formatValue(indicator.current_value, indicator.unit);
        document.getElementById('modal-date').textContent =
            `As of ${Utils.formatDate(indicator.current_date)}`;

        // Status
        const statusEl = document.getElementById('modal-status');
        statusEl.innerHTML = `
            <span class="status-badge ${indicator.status}">
                ${Utils.getStatusLabel(indicator.status)}
            </span>
        `;

        // Trend
        const trendEl = document.getElementById('modal-trend');
        trendEl.className = `stat-desc ${Utils.getTrendClass(indicator.trend)}`;
        trendEl.textContent = `${Utils.getTrendIcon(indicator.trend)} ${Utils.getTrendLabel(indicator.trend)}`;

        // Change
        const changePrefix = indicator.change_value >= 0 ? '+' : '';
        document.getElementById('modal-change').textContent =
            `${changePrefix}${Utils.formatNumber(indicator.change_value)}`;
        document.getElementById('modal-change-pct').textContent =
            `${changePrefix}${Utils.formatNumber(indicator.change_percent)}%`;

        // Show modal
        modal.showModal();

        // Load full data and create chart
        try {
            const fullData = await Utils.fetchJSON(`data/${category}/${indicator.id}.json`);

            // Update thresholds info
            this.updateThresholdsInfo(fullData.thresholds, fullData.unit);

            // Create detail chart
            Charts.createDetailChart(fullData.data, {
                ...indicator,
                thresholds: fullData.thresholds
            });

        } catch (error) {
            console.error('Failed to load indicator details:', error);
            document.getElementById('modal-thresholds').innerHTML = `
                <div class="alert alert-warning">
                    <span>Unable to load full historical data</span>
                </div>
            `;

            // Fall back to sparkline data
            Charts.createDetailChart(indicator.sparkline, indicator);
        }
    },

    /**
     * Update thresholds information in the modal
     */
    updateThresholdsInfo(thresholds, unit) {
        const container = document.getElementById('modal-thresholds');

        if (!thresholds) {
            container.innerHTML = '';
            return;
        }

        const items = [];

        if (thresholds.green_max !== null || thresholds.green_min !== null) {
            const greenText = thresholds.invert
                ? `Above ${thresholds.green_min}${unit}`
                : `Below ${thresholds.green_max}${unit}`;
            items.push(`<span class="text-success">Healthy:</span> ${greenText}`);
        }

        if (thresholds.yellow_max !== null || thresholds.yellow_min !== null) {
            const value = thresholds.yellow_max || thresholds.yellow_min;
            items.push(`<span class="text-warning">Caution:</span> Around ${value}${unit}`);
        }

        if (thresholds.red_min !== null || thresholds.red_max !== null) {
            const redText = thresholds.invert
                ? `Below ${thresholds.yellow_min || thresholds.red_max}${unit}`
                : `Above ${thresholds.red_min || thresholds.yellow_max}${unit}`;
            items.push(`<span class="text-error">Warning:</span> ${redText}`);
        }

        container.innerHTML = `
            <div class="flex flex-wrap gap-4 text-sm">
                ${items.map(item => `<div>${item}</div>`).join('')}
            </div>
        `;
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());

// Make available globally for debugging
window.App = App;
