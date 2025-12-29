/**
 * Smart Property Finder - Frontend Application
 * Loads pre-scraped property data and provides filtering/sorting
 */

// Configuration
const CONFIG = {
    dataUrl: 'data/properties.json',
    refreshInterval: null, // No auto-refresh for static site
    defaultFilters: {
        maxPrice: 100000,
        minScore: 0,
        types: ['house', 'flat'],
        conditions: ['distressed', 'fixer', 'standard'],
        sources: ['rightmove', 'zoopla', 'auction']
    }
};

// State
let allProperties = [];
let filteredProperties = [];
let currentFilters = { ...CONFIG.defaultFilters };

// DOM Elements
const elements = {
    locationFilter: document.getElementById('location-filter'),
    priceMax: document.getElementById('price-max'),
    priceMaxDisplay: document.getElementById('price-max-display'),
    scoreMin: document.getElementById('score-min'),
    scoreMinDisplay: document.getElementById('score-min-display'),
    sortBy: document.getElementById('sort-by'),
    resetFilters: document.getElementById('reset-filters'),
    resultsCount: document.getElementById('results-count'),
    lastUpdated: document.getElementById('last-updated'),
    loading: document.getElementById('loading'),
    error: document.getElementById('error'),
    noResults: document.getElementById('no-results'),
    resultsGrid: document.getElementById('results-grid')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupEventListeners();
    await loadProperties();
}

function setupEventListeners() {
    // Price slider
    elements.priceMax.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        elements.priceMaxDisplay.textContent = formatPrice(value);
        currentFilters.maxPrice = value;
        applyFilters();
    });

    // Score slider
    elements.scoreMin.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        elements.scoreMinDisplay.textContent = value;
        currentFilters.minScore = value;
        applyFilters();
    });

    // Location dropdown
    elements.locationFilter.addEventListener('change', () => {
        applyFilters();
    });

    // Sort dropdown
    elements.sortBy.addEventListener('change', () => {
        applyFilters();
    });

    // Checkbox filters
    document.querySelectorAll('.checkbox-group input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateCheckboxFilters();
            applyFilters();
        });
    });

    // Reset button
    elements.resetFilters.addEventListener('click', resetFilters);
}

function updateCheckboxFilters() {
    // Property types
    currentFilters.types = [];
    document.querySelectorAll('.filter-group:has(input[value="house"]) input:checked').forEach(cb => {
        currentFilters.types.push(cb.value);
    });

    // Conditions
    currentFilters.conditions = [];
    document.querySelectorAll('.filter-group:has(input[value="distressed"]) input:checked').forEach(cb => {
        currentFilters.conditions.push(cb.value);
    });

    // Sources
    currentFilters.sources = [];
    document.querySelectorAll('.filter-group:has(input[value="rightmove"]) input:checked').forEach(cb => {
        currentFilters.sources.push(cb.value);
    });
}

async function loadProperties() {
    showLoading(true);
    hideError();

    try {
        const response = await fetch(CONFIG.dataUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        allProperties = data.properties || [];
        
        // Update last updated timestamp
        if (data.lastUpdated) {
            elements.lastUpdated.textContent = formatDate(data.lastUpdated);
        } else {
            elements.lastUpdated.textContent = 'Unknown';
        }

        // Populate location filter
        populateLocationFilter();

        // Apply initial filters
        applyFilters();

    } catch (error) {
        console.error('Failed to load properties:', error);
        showError();
    } finally {
        showLoading(false);
    }
}

function populateLocationFilter() {
    const locations = [...new Set(allProperties.map(p => p.location).filter(Boolean))];
    locations.sort();

    elements.locationFilter.innerHTML = '<option value="">All Locations</option>';
    locations.forEach(loc => {
        const option = document.createElement('option');
        option.value = loc;
        option.textContent = loc;
        elements.locationFilter.appendChild(option);
    });
}

function applyFilters() {
    const selectedLocation = elements.locationFilter.value;

    filteredProperties = allProperties.filter(property => {
        // Price filter
        const price = property.price || 0;
        if (price > currentFilters.maxPrice && price > 0) return false;

        // Score filter
        const score = property.score || 0;
        if (score < currentFilters.minScore) return false;

        // Location filter
        if (selectedLocation && property.location !== selectedLocation) return false;

        // Type filter
        const type = detectPropertyType(property);
        if (!currentFilters.types.includes(type)) return false;

        // Condition filter
        const condition = detectCondition(property);
        if (!currentFilters.conditions.includes(condition)) return false;

        // Source filter
        const source = detectSource(property);
        if (!currentFilters.sources.includes(source)) return false;

        return true;
    });

    // Sort
    sortProperties();

    // Render
    renderProperties();
}

function detectPropertyType(property) {
    const title = (property.title || '').toLowerCase();
    const desc = (property.description || '').toLowerCase();
    const combined = title + ' ' + desc;

    if (combined.includes('land') || combined.includes('plot')) return 'land';
    if (combined.includes('flat') || combined.includes('apartment')) return 'flat';
    return 'house';
}

function detectCondition(property) {
    const category = (property.category || '').toLowerCase();
    const desc = (property.description || '').toLowerCase();

    if (category.includes('distressed') || desc.includes('derelict') || desc.includes('fire damage')) {
        return 'distressed';
    }
    if (category.includes('fixer') || desc.includes('modernisation') || desc.includes('refurbishment')) {
        return 'fixer';
    }
    return 'standard';
}

function detectSource(property) {
    const agent = (property.agent || '').toLowerCase();
    const url = (property.url || '').toLowerCase();

    if (url.includes('rightmove') || agent.includes('rightmove')) return 'rightmove';
    if (url.includes('zoopla') || agent.includes('zoopla')) return 'zoopla';
    if (url.includes('auction') || agent.includes('auction') || agent.includes('pugh')) return 'auction';
    return 'rightmove'; // Default
}

function sortProperties() {
    const sortBy = elements.sortBy.value;

    filteredProperties.sort((a, b) => {
        switch (sortBy) {
            case 'score-desc':
                return (b.score || 0) - (a.score || 0);
            case 'price-asc':
                return (a.price || 0) - (b.price || 0);
            case 'price-desc':
                return (b.price || 0) - (a.price || 0);
            default:
                return 0;
        }
    });
}

function renderProperties() {
    elements.resultsCount.textContent = `(${filteredProperties.length})`;

    if (filteredProperties.length === 0) {
        elements.resultsGrid.innerHTML = '';
        elements.noResults.classList.remove('hidden');
        return;
    }

    elements.noResults.classList.add('hidden');
    elements.resultsGrid.innerHTML = filteredProperties.map(renderPropertyCard).join('');
}

function renderPropertyCard(property) {
    const price = property.price ? formatPrice(property.price) : (property.price_display || 'POA');
    const score = property.score || 0;
    const scoreClass = score >= 7 ? 'score-high' : score >= 4 ? 'score-medium' : 'score-low';
    
    const type = detectPropertyType(property);
    const condition = detectCondition(property);
    const source = detectSource(property);

    const tags = [];
    if (condition === 'distressed') tags.push('<span class="tag tag-distressed">Distressed</span>');
    if (condition === 'fixer') tags.push('<span class="tag tag-fixer">Fixer Upper</span>');
    if (source === 'auction') tags.push('<span class="tag tag-auction">Auction</span>');
    tags.push(`<span class="tag tag-source">${capitalizeFirst(source)}</span>`);

    const description = truncate(property.description || 'No description available.', 150);

    return `
        <article class="property-card">
            <div class="card-header">
                <span class="card-price">${price}</span>
                <span class="card-score ${scoreClass}">⭐ ${score.toFixed(1)}</span>
            </div>
            <div class="card-body">
                <h3 class="card-title">${escapeHtml(property.title || 'Property')}</h3>
                <p class="card-address">📍 ${escapeHtml(property.address || 'Address not available')}</p>
                <div class="card-tags">${tags.join('')}</div>
                <p class="card-description">${escapeHtml(description)}</p>
            </div>
            <div class="card-footer">
                <a href="${escapeHtml(property.url || '#')}" target="_blank" rel="noopener" class="card-link">
                    View Property →
                </a>
            </div>
        </article>
    `;
}

function resetFilters() {
    // Reset sliders
    elements.priceMax.value = CONFIG.defaultFilters.maxPrice;
    elements.priceMaxDisplay.textContent = formatPrice(CONFIG.defaultFilters.maxPrice);
    elements.scoreMin.value = CONFIG.defaultFilters.minScore;
    elements.scoreMinDisplay.textContent = CONFIG.defaultFilters.minScore;

    // Reset dropdowns
    elements.locationFilter.value = '';
    elements.sortBy.value = 'score-desc';

    // Reset checkboxes - types
    document.querySelectorAll('.filter-group:has(input[value="house"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.types.includes(cb.value);
    });

    // Reset checkboxes - conditions
    document.querySelectorAll('.filter-group:has(input[value="distressed"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.conditions.includes(cb.value);
    });

    // Reset checkboxes - sources
    document.querySelectorAll('.filter-group:has(input[value="rightmove"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.sources.includes(cb.value);
    });

    // Reset state
    currentFilters = { ...CONFIG.defaultFilters };

    // Re-apply
    applyFilters();
}

// Utility functions
function formatPrice(price) {
    return '£' + price.toLocaleString('en-GB');
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

function truncate(str, maxLength) {
    if (str.length <= maxLength) return str;
    return str.slice(0, maxLength).trim() + '...';
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showLoading(show) {
    elements.loading.classList.toggle('hidden', !show);
}

function showError() {
    elements.error.classList.remove('hidden');
}

function hideError() {
    elements.error.classList.add('hidden');
}
