/**
 * Smart Property Finder - Frontend Application
 * Loads pre-scraped property data and provides filtering/sorting
 */

// Configuration
const CONFIG = {
    dataUrl: 'data/properties.json',
    refreshInterval: null, // No auto-refresh for static site
    defaultFilters: {
        minPrice: 0,
        maxPrice: 150000,
        minScore: 0,
        postcode: '',
        excludeKeywords: '',
        types: ['house', 'flat'],
        conditions: ['distressed', 'fixer', 'standard'],
        sources: ['rightmove', 'zoopla', 'onthemarket', 'boomin', 'purplebricks', 'auction'],
        tenures: ['freehold', 'leasehold', 'unknown'],
        excludeAuctions: false
    }
};

// State
let allProperties = [];
let filteredProperties = [];
let currentFilters = { ...CONFIG.defaultFilters };
let displayedCount = 0;
const BATCH_SIZE = 24;
let debouncedApplyFilters;

// DOM Elements
const elements = {
    locationFilter: document.getElementById('location-filter'),
    postcodeFilter: document.getElementById('postcode-filter'),
    excludeKeywords: document.getElementById('exclude-keywords'),
    priceMin: document.getElementById('price-min'),
    priceMinDisplay: document.getElementById('price-min-display'),
    priceMax: document.getElementById('price-max'),
    priceMaxDisplay: document.getElementById('price-max-display'),
    scoreMin: document.getElementById('score-min'),
    scoreMinDisplay: document.getElementById('score-min-display'),
    sortBy: document.getElementById('sort-by'),
    resetFilters: document.getElementById('reset-filters'),
    resultsCount: document.getElementById('results-count'),
    lastUpdated: document.getElementById('last-updated'),
    headerLastUpdated: document.getElementById('header-last-updated'),
    nextRefresh: document.getElementById('next-refresh'),
    loading: document.getElementById('loading'),
    error: document.getElementById('error'),
    noResults: document.getElementById('no-results'),
    resultsGrid: document.getElementById('results-grid')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupEventListeners();
    setupInfiniteScroll();
    await loadProperties();
    updateNextRefreshCountdown(); // Start countdown
    setInterval(updateNextRefreshCountdown, 60000); // Update every minute
}

function setupEventListeners() {
    // Initialize debounced filter function
    debouncedApplyFilters = debounce(() => applyFilters(), 300);

    // Min Price slider
    if (elements.priceMin) {
        elements.priceMin.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            elements.priceMinDisplay.textContent = formatPrice(value);
            currentFilters.minPrice = value;
            debouncedApplyFilters();
        });
    }

    // Max Price slider
    elements.priceMax.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        elements.priceMaxDisplay.textContent = formatPrice(value);
        currentFilters.maxPrice = value;
        debouncedApplyFilters();
    });

    // Score slider
    elements.scoreMin.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        elements.scoreMinDisplay.textContent = value;
        currentFilters.minScore = value;
        debouncedApplyFilters();
    });

    // Location dropdown
    elements.locationFilter.addEventListener('change', () => {
        applyFilters();
    });

    // Postcode input
    if (elements.postcodeFilter) {
        elements.postcodeFilter.addEventListener('input', (e) => {
            currentFilters.postcode = e.target.value;
            debouncedApplyFilters();
        });
    }

    // Exclude Keywords input
    if (elements.excludeKeywords) {
        elements.excludeKeywords.addEventListener('input', (e) => {
            currentFilters.excludeKeywords = e.target.value;
            debouncedApplyFilters();
        });
    }

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

    // Tenures
    currentFilters.tenures = [];
    document.querySelectorAll('.filter-group:has(input[value="freehold"]) input:checked').forEach(cb => {
        currentFilters.tenures.push(cb.value);
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

    // Exclude Auctions toggle
    const excludeAuctionsCheckbox = document.getElementById('exclude-auctions');
    currentFilters.excludeAuctions = excludeAuctionsCheckbox ? excludeAuctionsCheckbox.checked : false;
    
    // If exclude auctions is checked, also uncheck the auction source
    if (currentFilters.excludeAuctions) {
        const auctionCheckbox = document.querySelector('.filter-group:has(input[value="rightmove"]) input[value="auction"]');
        if (auctionCheckbox) {
            auctionCheckbox.checked = false;
            currentFilters.sources = currentFilters.sources.filter(s => s !== 'auction');
        }
    }
}

async function loadProperties() {
    showLoading(true);
    hideError();

    try {
        // Add timestamp to prevent caching
        const url = `${CONFIG.dataUrl}?t=${new Date().getTime()}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        allProperties = data.properties || [];
        
        // Update last updated timestamp
        if (data.lastUpdated) {
            const formattedDate = formatDate(data.lastUpdated);
            const relativeTime = formatRelativeTime(data.lastUpdated);
            elements.lastUpdated.textContent = formattedDate;
            if (elements.headerLastUpdated) {
                elements.headerLastUpdated.textContent = relativeTime;
            }
        } else {
            elements.lastUpdated.textContent = 'Unknown';
            if (elements.headerLastUpdated) {
                elements.headerLastUpdated.textContent = 'Unknown';
            }
        }

        // Populate location filter
        populateLocationFilter(data.locations);

        // Update Stats Box
        updateStatsBox();

        // Apply initial filters
        applyFilters();

    } catch (error) {
        console.error('Failed to load properties:', error);
        showError();
    } finally {
        showLoading(false);
    }
}

function updateStatsBox() {
    const total = allProperties.length;
    const highRoi = allProperties.filter(p => (p.roi || 0) > 8).length;
    
    const totalEl = document.getElementById('stat-total-properties');
    const roiEl = document.getElementById('stat-high-roi');
    
    if (totalEl) totalEl.textContent = total.toLocaleString();
    if (roiEl) roiEl.textContent = highRoi.toLocaleString();
}

function populateLocationFilter(providedLocations) {
    let locations;
    
    if (providedLocations && Array.isArray(providedLocations) && providedLocations.length > 0) {
        locations = providedLocations;
    } else {
        // Fallback to extracting from properties
        locations = [...new Set(allProperties.map(p => p.location).filter(Boolean))];
        locations.sort();
    }

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
        // Price filter (min and max)
        const price = property.price || 0;
        
        // Fix: If min price is set (>0), exclude POA/0 price items
        if (currentFilters.minPrice > 0 && price === 0) return false;

        if (price > 0) {
            if (price < currentFilters.minPrice) return false;
            if (price > currentFilters.maxPrice) return false;
        }

        // Score filter
        const score = property.score || 0;
        if (score < currentFilters.minScore) return false;

        // Location filter
        if (selectedLocation && property.location !== selectedLocation) return false;

        // Postcode filter
        if (currentFilters.postcode) {
            const searchTerms = currentFilters.postcode.toLowerCase().split(',').map(t => t.trim()).filter(t => t);
            if (searchTerms.length > 0) {
                const address = (property.address || '').toLowerCase();
                // Check if address contains ANY of the search terms
                const matches = searchTerms.some(term => address.includes(term));
                if (!matches) return false;
            }
        }

        // Exclude Keywords filter
        if (currentFilters.excludeKeywords) {
            const excludeTerms = currentFilters.excludeKeywords.toLowerCase().split(',').map(t => t.trim()).filter(t => t);
            if (excludeTerms.length > 0) {
                const description = (property.description || '').toLowerCase();
                const title = (property.title || '').toLowerCase();
                const combinedText = title + ' ' + description;
                
                // Check if text contains ANY of the exclude terms
                const hasExcludedTerm = excludeTerms.some(term => combinedText.includes(term));
                if (hasExcludedTerm) return false;
            }
        }

        // Type filter
        const type = detectPropertyType(property);
        if (!currentFilters.types.includes(type)) return false;

        // Tenure filter
        const tenure = detectTenure(property);
        if (!currentFilters.tenures.includes(tenure)) return false;

        // Condition filter
        const condition = detectCondition(property);
        if (!currentFilters.conditions.includes(condition)) return false;

        // Source filter
        const source = detectSource(property);
        if (!currentFilters.sources.includes(source)) return false;

        // Exclude auctions filter
        if (currentFilters.excludeAuctions && isAuctionProperty(property)) return false;

        return true;
    });

    // Sort
    sortProperties();

    // Render
    renderProperties();
}

function detectTenure(property) {
    const tenure = (property.tenure || '').toLowerCase();
    
    if (tenure.includes('freehold')) return 'freehold';
    if (tenure.includes('leasehold')) return 'leasehold';
    return 'unknown';
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
    if (url.includes('onthemarket')) return 'onthemarket';
    if (url.includes('boomin') || agent.includes('boomin')) return 'boomin';
    if (url.includes('purplebricks') || agent.includes('purplebricks')) return 'purplebricks';
    if (url.includes('auction') || agent.includes('auction') || agent.includes('pugh')) return 'auction';
    return 'rightmove'; // Default
}

function isAuctionProperty(property) {
    const source = detectSource(property);
    const agent = (property.agent || '').toLowerCase();
    const title = (property.title || '').toLowerCase();
    const desc = (property.description || '').toLowerCase();
    
    // Check if source is auction
    if (source === 'auction') return true;
    
    // Check for auction keywords in agent, title, or description
    const auctionKeywords = ['auction', 'auctioneer', 'lot ', 'guide price', 'reserve price'];
    for (const keyword of auctionKeywords) {
        if (agent.includes(keyword) || title.includes(keyword) || desc.includes(keyword)) {
            return true;
        }
    }
    
    return false;
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
    
    // Reset pagination
    displayedCount = 0;
    elements.resultsGrid.innerHTML = '';
    
    // Render first batch
    renderBatch();
}

function renderBatch() {
    const nextBatch = filteredProperties.slice(displayedCount, displayedCount + BATCH_SIZE);
    
    if (nextBatch.length > 0) {
        const html = nextBatch.map(renderPropertyCard).join('');
        elements.resultsGrid.insertAdjacentHTML('beforeend', html);
        displayedCount += nextBatch.length;
    }
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

    // ROI Section
    let roiHtml = '';
    if (property.roi) {
        const roiClass = property.roi > 8 ? 'text-success' : 'text-warning';
        roiHtml = `
            <div class="card-roi">
                <div class="roi-metric">
                    <span class="roi-label">Est. ROI</span>
                    <span class="roi-value ${roiClass}">${property.roi}%</span>
                </div>
                <div class="roi-details">
                    <span>Avg Rent: £${property.avg_area_rent ? property.avg_area_rent.toLocaleString() : '?'}</span>
                    <span>Avg Price: £${property.avg_area_price ? property.avg_area_price.toLocaleString() : '?'}</span>
                </div>
            </div>
        `;
    } else if (property.avg_area_price) {
        // Auction / No Price
        roiHtml = `
            <div class="card-roi">
                <div class="roi-metric">
                    <span class="roi-label">Area Avg</span>
                    <span class="roi-value">£${property.avg_area_price.toLocaleString()}</span>
                </div>
                <div class="roi-details">
                    <span>Potential Value Indicator</span>
                </div>
            </div>
        `;
    }

    return `
        <article class="property-card">
            <div class="card-header">
                <span class="card-price">${price}</span>
                <span class="card-score ${scoreClass}">⭐ ${score.toFixed(1)}</span>
            </div>
            <div class="card-body">
                <h3 class="card-title">${escapeHtml(property.title || 'Property')}</h3>
                <p class="card-address">📍 ${escapeHtml(property.address || 'Address not available')}</p>
                ${roiHtml}
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
    if (elements.priceMin) {
        elements.priceMin.value = CONFIG.defaultFilters.minPrice;
        elements.priceMinDisplay.textContent = formatPrice(CONFIG.defaultFilters.minPrice);
    }
    elements.priceMax.value = CONFIG.defaultFilters.maxPrice;
    elements.priceMaxDisplay.textContent = formatPrice(CONFIG.defaultFilters.maxPrice);
    elements.scoreMin.value = CONFIG.defaultFilters.minScore;
    elements.scoreMinDisplay.textContent = CONFIG.defaultFilters.minScore;

    // Reset dropdowns
    elements.locationFilter.value = '';
    if (elements.postcodeFilter) elements.postcodeFilter.value = '';
    elements.sortBy.value = 'score-desc';

    // Reset checkboxes - types
    document.querySelectorAll('.filter-group:has(input[value="house"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.types.includes(cb.value);
    });

    // Reset checkboxes - tenures
    document.querySelectorAll('.filter-group:has(input[value="freehold"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.tenures.includes(cb.value);
    });

    // Reset checkboxes - conditions
    document.querySelectorAll('.filter-group:has(input[value="distressed"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.conditions.includes(cb.value);
    });

    // Reset checkboxes - sources
    document.querySelectorAll('.filter-group:has(input[value="rightmove"]) input').forEach(cb => {
        cb.checked = CONFIG.defaultFilters.sources.includes(cb.value);
    });

    // Reset exclude auctions toggle
    const excludeAuctionsCheckbox = document.getElementById('exclude-auctions');
    if (excludeAuctionsCheckbox) {
        excludeAuctionsCheckbox.checked = CONFIG.defaultFilters.excludeAuctions;
    }

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

function formatRelativeTime(dateString) {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return formatDate(dateString);
    } catch {
        return dateString;
    }
}

function updateNextRefreshCountdown() {
    // GitHub Actions runs at 6 AM UTC daily
    const now = new Date();
    const nextRefresh = new Date(now);
    nextRefresh.setUTCHours(6, 0, 0, 0);
    
    // If it's past 6 AM UTC today, next refresh is tomorrow
    if (now.getUTCHours() >= 6) {
        nextRefresh.setUTCDate(nextRefresh.getUTCDate() + 1);
    }
    
    const diffMs = nextRefresh - now;
    const diffHours = Math.floor(diffMs / 3600000);
    const diffMins = Math.floor((diffMs % 3600000) / 60000);
    
    let text;
    if (diffHours > 0) {
        text = `${diffHours}h ${diffMins}m`;
    } else {
        text = `${diffMins}m`;
    }
    
    if (elements.nextRefresh) {
        elements.nextRefresh.textContent = text;
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

// Performance Utilities
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Infinite Scroll
let observer;
let sentinel;

function setupInfiniteScroll() {
    // Create sentinel element if it doesn't exist
    if (!sentinel) {
        sentinel = document.createElement('div');
        sentinel.id = 'scroll-sentinel';
        sentinel.style.height = '20px';
        sentinel.style.width = '100%';
        // Insert after results grid
        elements.resultsGrid.parentNode.insertBefore(sentinel, elements.resultsGrid.nextSibling);
    }

    const options = {
        root: null,
        rootMargin: '200px',
        threshold: 0.1
    };

    if (observer) observer.disconnect();

    observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && displayedCount < filteredProperties.length) {
                renderBatch();
            }
        });
    }, options);

    observer.observe(sentinel);
}
