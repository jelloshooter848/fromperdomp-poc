// DOMP Marketplace Web Application
class DOMPMarketplace {
    constructor() {
        this.apiBase = '/api';
        this.websocket = null;
        this.listings = [];
        this.currentSection = 'marketplace';
        this.init();
    }

    async init() {
        await this.loadUserData();
        await this.loadListings();
        this.setupWebSocket();
        this.setupEventListeners();
        this.showNotification('Connected to DOMP Marketplace', 'success');
    }

    // WebSocket connection for real-time updates
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.websocket = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        this.websocket.onopen = () => {
            this.updateConnectionStatus(true);
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            this.updateConnectionStatus(false);
            // Reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };
        
        this.websocket.onerror = () => {
            this.updateConnectionStatus(false);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_listing':
                this.showNotification(`New listing: ${data.product_name}`, 'info');
                this.loadListings();
                break;
            case 'bid_accepted':
                this.showNotification(`Bid accepted for ${data.product_name}!`, 'success');
                this.loadTransactions();
                break;
            case 'connected':
                console.log('WebSocket connected:', data.message);
                break;
        }
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        if (connected) {
            statusEl.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="bi bi-wifi"></i> Connected to DOMP Network
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        } else {
            statusEl.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <i class="bi bi-wifi-off"></i> Reconnecting to DOMP Network...
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }

    // Load user data
    async loadUserData() {
        try {
            const response = await fetch(`${this.apiBase}/identity`);
            const data = await response.json();
            
            document.getElementById('userPubkey').textContent = data.pubkey_short;
            
            const balanceResponse = await fetch(`${this.apiBase}/wallet/balance`);
            const balanceData = await balanceResponse.json();
            document.getElementById('walletBalance').textContent = 
                balanceData.balance_sats.toLocaleString();
                
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showNotification('Error loading user data', 'error');
        }
    }

    // Load marketplace listings
    async loadListings() {
        try {
            const response = await fetch(`${this.apiBase}/listings`);
            const data = await response.json();
            this.listings = data.listings;
            this.renderListings();
        } catch (error) {
            console.error('Error loading listings:', error);
            this.showNotification('Error loading listings', 'error');
        }
    }

    // Render listings in the UI
    renderListings() {
        const container = document.getElementById('listingsContainer');
        
        if (this.listings.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-shop display-1 text-muted"></i>
                    <h3 class="text-muted">No listings available</h3>
                    <p class="text-muted">Be the first to create a listing!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.listings.map(listing => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card listing-card h-100" onclick="showItemDetails('${listing.id}')">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <h5 class="card-title mb-0">${listing.product_name}</h5>
                            <span class="badge bg-secondary">${listing.category}</span>
                        </div>
                        
                        <p class="card-text text-muted">${listing.description.substring(0, 100)}${listing.description.length > 100 ? '...' : ''}</p>
                        
                        <div class="mb-3">
                            <span class="price-badge">
                                <i class="bi bi-lightning-fill"></i>
                                ${listing.price_sats.toLocaleString()} sats
                            </span>
                            <small class="text-muted ms-2">(${listing.price_btc.toFixed(6)} BTC)</small>
                        </div>

                        <div class="seller-info">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <small class="text-muted">
                                    <i class="bi bi-person-circle"></i> ${listing.seller.pubkey_short}
                                </small>
                                <span class="trust-score">${listing.seller.trust_score.toFixed(3)}</span>
                            </div>
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div class="reputation-stars">
                                    ${this.renderStars(listing.seller.rating)}
                                    <small class="text-muted">(${listing.seller.total_transactions})</small>
                                </div>
                                <span class="badge ${this.getReliabilityClass(listing.seller.reliability)}">
                                    ${listing.seller.reliability}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) {
            stars += '<i class="bi bi-star-fill"></i>';
        }
        
        if (hasHalfStar) {
            stars += '<i class="bi bi-star-half"></i>';
        }
        
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < emptyStars; i++) {
            stars += '<i class="bi bi-star"></i>';
        }
        
        return stars;
    }

    getReliabilityClass(reliability) {
        switch (reliability) {
            case 'Excellent': return 'bg-success';
            case 'Good': return 'bg-info';
            case 'New Seller': return 'bg-warning';
            case 'Limited Data': return 'bg-secondary';
            default: return 'bg-secondary';
        }
    }

    // Show item details modal
    async showItemDetails(listingId) {
        try {
            const response = await fetch(`${this.apiBase}/listings/${listingId}`);
            const listing = await response.json();
            
            const modalTitle = document.getElementById('itemModalTitle');
            const modalBody = document.getElementById('itemModalBody');
            
            modalTitle.textContent = listing.product_name;
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="text-muted">Description</h6>
                        <p>${listing.description}</p>
                        
                        <h6 class="text-muted">Details</h6>
                        <ul class="list-unstyled">
                            <li><strong>Category:</strong> ${listing.category}</li>
                            <li><strong>Price:</strong> ${listing.price_sats.toLocaleString()} sats (${listing.price_btc.toFixed(6)} BTC)</li>
                            <li><strong>Seller Collateral:</strong> ${listing.seller_collateral_sats.toLocaleString()} sats</li>
                            <li><strong>Listed:</strong> ${new Date(listing.created_at * 1000).toLocaleDateString()}</li>
                        </ul>
                        
                        <button class="btn btn-primary" onclick="showPurchaseModal('${listing.id}')">
                            <i class="bi bi-lightning-fill"></i> Purchase with Lightning
                        </button>
                    </div>
                    <div class="col-md-4">
                        <h6 class="text-muted">Seller Reputation</h6>
                        <div class="card">
                            <div class="card-body">
                                <div class="text-center mb-3">
                                    <div class="reputation-stars fs-4">
                                        ${this.renderStars(listing.seller.rating)}
                                    </div>
                                    <p class="mb-1">${listing.seller.rating.toFixed(1)}/5.0</p>
                                    <span class="badge ${this.getReliabilityClass(listing.seller.reliability)}">
                                        ${listing.seller.reliability}
                                    </span>
                                </div>
                                
                                <ul class="list-unstyled mb-0">
                                    <li><strong>Trust Score:</strong> ${listing.seller.trust_score.toFixed(3)}</li>
                                    <li><strong>Transactions:</strong> ${listing.seller.total_transactions}</li>
                                    <li><strong>Verified Purchases:</strong> ${listing.seller.verified_purchases}</li>
                                    <li><strong>Completed Escrows:</strong> ${listing.seller.completed_escrows}</li>
                                    <li><strong>Unique Reviewers:</strong> ${listing.seller.unique_reviewers}</li>
                                </ul>
                                
                                ${listing.seller.item_quality ? `
                                    <hr>
                                    <h6 class="text-muted">Detailed Metrics</h6>
                                    <ul class="list-unstyled mb-0">
                                        <li><strong>Item Quality:</strong> ${listing.seller.item_quality.toFixed(1)}/5.0</li>
                                        <li><strong>Shipping Speed:</strong> ${listing.seller.shipping_speed.toFixed(1)}/5.0</li>
                                        <li><strong>Communication:</strong> ${listing.seller.communication.toFixed(1)}/5.0</li>
                                    </ul>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            new bootstrap.Modal(document.getElementById('itemModal')).show();
            
        } catch (error) {
            console.error('Error loading item details:', error);
            this.showNotification('Error loading item details', 'error');
        }
    }

    // Show purchase modal
    showPurchaseModal(listingId) {
        const listing = this.listings.find(l => l.id === listingId);
        if (!listing) return;
        
        const modalBody = document.getElementById('purchaseModalBody');
        modalBody.innerHTML = `
            <div class="mb-3">
                <h6>${listing.product_name}</h6>
                <p class="text-muted">${listing.description.substring(0, 100)}...</p>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Bid Amount (satoshis)</label>
                <input type="number" class="form-control" id="bidAmount" value="${listing.price_sats}" min="1">
                <small class="text-muted">Listed price: ${listing.price_sats.toLocaleString()} sats</small>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Message (optional)</label>
                <input type="text" class="form-control" id="bidMessage" placeholder="I'm interested in purchasing...">
            </div>
            
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                <strong>Lightning Escrow:</strong> Your payment will be secured in a Lightning HTLC until you confirm receipt.
                Collateral required: ${listing.price_sats.toLocaleString()} sats
            </div>
            
            <div class="d-grid">
                <button class="btn btn-primary" onclick="placeBid('${listingId}')">
                    <i class="bi bi-lightning-fill"></i> Place Bid & Start Escrow
                </button>
            </div>
        `;
        
        new bootstrap.Modal(document.getElementById('purchaseModal')).show();
    }

    // Place a bid
    async placeBid(listingId) {
        const bidAmount = document.getElementById('bidAmount').value;
        const bidMessage = document.getElementById('bidMessage').value;
        
        if (!bidAmount || bidAmount <= 0) {
            this.showNotification('Invalid bid amount', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/bids`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    listing_id: listingId,
                    bid_amount_sats: parseInt(bidAmount),
                    message: bidMessage
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                bootstrap.Modal.getInstance(document.getElementById('purchaseModal')).hide();
                this.loadUserData(); // Refresh balance
                
                // Auto-switch to transactions tab
                setTimeout(() => {
                    this.showSection('transactions');
                }, 1000);
            } else {
                this.showNotification('Failed to place bid', 'error');
            }
            
        } catch (error) {
            console.error('Error placing bid:', error);
            this.showNotification('Error placing bid', 'error');
        }
    }

    // Create a new listing
    async createListing(formData) {
        try {
            const response = await fetch(`${this.apiBase}/listings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                document.getElementById('createListingForm').reset();
                this.loadListings();
            } else {
                this.showNotification('Failed to create listing', 'error');
            }
            
        } catch (error) {
            console.error('Error creating listing:', error);
            this.showNotification('Error creating listing', 'error');
        }
    }

    // Load user transactions
    async loadTransactions() {
        try {
            const response = await fetch(`${this.apiBase}/transactions`);
            const data = await response.json();
            this.renderTransactions(data.transactions);
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.showNotification('Error loading transactions', 'error');
        }
    }

    // Render transactions
    renderTransactions(transactions) {
        const container = document.getElementById('transactionsContainer');
        
        if (transactions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-receipt display-1 text-muted"></i>
                    <h3 class="text-muted">No transactions yet</h3>
                    <p class="text-muted">Your purchases will appear here</p>
                </div>
            `;
            return;
        }

        container.innerHTML = transactions.map(tx => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h6 class="mb-1">${tx.product_name}</h6>
                            <small class="text-muted">Transaction ID: ${tx.id}</small>
                        </div>
                        <div class="col-md-3 text-end">
                            <strong>${tx.amount_sats.toLocaleString()} sats</strong><br>
                            <small class="text-muted">${tx.amount_btc.toFixed(6)} BTC</small>
                        </div>
                        <div class="col-md-3 text-end">
                            <span class="status-badge status-${tx.status}">${tx.status}</span><br>
                            <small class="text-muted">${new Date(tx.created_at * 1000).toLocaleDateString()}</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Load reputation analytics
    async loadReputationAnalytics() {
        try {
            const response = await fetch(`${this.apiBase}/reputation/analytics`);
            const data = await response.json();
            this.renderReputationAnalytics(data);
        } catch (error) {
            console.error('Error loading reputation analytics:', error);
            this.showNotification('Error loading reputation analytics', 'error');
        }
    }

    // Render reputation analytics
    renderReputationAnalytics(data) {
        const container = document.getElementById('analyticsContainer');
        container.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body">
                            <h3 class="text-primary">${data.total_sellers}</h3>
                            <p class="mb-0">Total Sellers</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body">
                            <h3 class="text-info">${data.total_listings}</h3>
                            <p class="mb-0">Active Listings</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body">
                            <h3 class="text-warning">${data.average_rating ? data.average_rating.toFixed(1) : 'N/A'}</h3>
                            <p class="mb-0">Average Rating</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body">
                            <h3 class="text-success">${data.total_volume_btc ? data.total_volume_btc.toFixed(3) : '0.000'}</h3>
                            <p class="mb-0">Total Volume (BTC)</p>
                        </div>
                    </div>
                </div>
            </div>
            
            ${data.rating_distribution ? `
                <div class="card">
                    <div class="card-body">
                        <h5><i class="bi bi-pie-chart"></i> Rating Distribution</h5>
                        <div class="row">
                            <div class="col-6 col-md-3 text-center">
                                <h4 class="text-success">${data.rating_distribution.excellent}</h4>
                                <small class="text-muted">Excellent (4.5+)</small>
                            </div>
                            <div class="col-6 col-md-3 text-center">
                                <h4 class="text-info">${data.rating_distribution.good}</h4>
                                <small class="text-muted">Good (3.5-4.4)</small>
                            </div>
                            <div class="col-6 col-md-3 text-center">
                                <h4 class="text-warning">${data.rating_distribution.average}</h4>
                                <small class="text-muted">Average (2.5-3.4)</small>
                            </div>
                            <div class="col-6 col-md-3 text-center">
                                <h4 class="text-danger">${data.rating_distribution.poor}</h4>
                                <small class="text-muted">Poor (<2.5)</small>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
    }

    // Load top sellers
    async loadTopSellers() {
        try {
            const response = await fetch(`${this.apiBase}/reputation/sellers`);
            const data = await response.json();
            this.renderTopSellers(data.sellers);
        } catch (error) {
            console.error('Error loading top sellers:', error);
            this.showNotification('Error loading top sellers', 'error');
        }
    }

    // Render top sellers
    renderTopSellers(sellers) {
        const container = document.getElementById('sellersContainer');
        
        if (sellers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-trophy display-1 text-muted"></i>
                    <h3 class="text-muted">No sellers with reputation data</h3>
                </div>
            `;
            return;
        }

        container.innerHTML = sellers.map((seller, index) => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-1 text-center">
                            <h3 class="text-primary">#${index + 1}</h3>
                        </div>
                        <div class="col-md-4">
                            <h6 class="mb-1">${seller.pubkey_short}</h6>
                            <span class="badge ${this.getReliabilityClass(seller.reliability)}">
                                ${seller.reliability}
                            </span>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="reputation-stars">
                                ${this.renderStars(seller.overall_score)}
                            </div>
                            <small class="text-muted">${seller.overall_score.toFixed(1)}/5.0</small>
                        </div>
                        <div class="col-md-2 text-center">
                            <strong>${seller.total_transactions}</strong><br>
                            <small class="text-muted">transactions</small>
                        </div>
                        <div class="col-md-2 text-center">
                            <span class="trust-score">${seller.trust_score.toFixed(3)}</span>
                            <br><small class="text-muted">${seller.total_volume_btc.toFixed(3)} BTC</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Navigation functions
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('d-none');
        });

        // Hide hero section for non-marketplace sections
        const heroSection = document.getElementById('heroSection');
        if (sectionName === 'marketplace') {
            heroSection.style.display = 'block';
        } else {
            heroSection.style.display = 'none';
        }

        // Show selected section
        document.getElementById(`${sectionName}Section`).classList.remove('d-none');

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        event.target.classList.add('active');

        // Load section-specific data
        this.currentSection = sectionName;
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'marketplace':
                await this.loadListings();
                break;
            case 'transactions':
                await this.loadTransactions();
                break;
            case 'reputation':
                await this.loadReputationAnalytics();
                break;
        }
    }

    showReputationTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.reputation-tab').forEach(tab => {
            tab.classList.add('d-none');
        });

        // Update navigation
        document.querySelectorAll('.nav-pills .nav-link').forEach(link => {
            link.classList.remove('active');
        });
        event.target.classList.add('active');

        // Show selected tab
        document.getElementById(`reputation${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`).classList.remove('d-none');

        // Load tab-specific data
        if (tabName === 'sellers') {
            this.loadTopSellers();
        }
    }

    // Filter listings by category
    filterListings() {
        const category = document.getElementById('categoryFilter').value;
        const filteredListings = category 
            ? this.listings.filter(listing => listing.category === category)
            : this.listings;
        
        // Temporarily store current listings and render filtered
        const originalListings = this.listings;
        this.listings = filteredListings;
        this.renderListings();
        this.listings = originalListings;
    }

    // Setup event listeners
    setupEventListeners() {
        // Create listing form
        document.getElementById('createListingForm').addEventListener('submit', (e) => {
            e.preventDefault();
            
            const formData = {
                product_name: document.getElementById('productName').value,
                description: document.getElementById('description').value,
                price_sats: parseInt(document.getElementById('priceSats').value),
                category: document.getElementById('category').value
            };
            
            this.createListing(formData);
        });
    }

    // Utility functions
    showNotification(message, type) {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Create a temporary container if it doesn't exist
        let alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alertContainer';
            alertContainer.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1050; max-width: 400px;';
            document.body.appendChild(alertContainer);
        }

        alertContainer.innerHTML = alertHtml;

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    }
}

// Global functions for onclick handlers
let marketplace;

function showSection(sectionName) {
    marketplace.showSection(sectionName);
}

function showReputationTab(tabName) {
    marketplace.showReputationTab(tabName);
}

function showItemDetails(listingId) {
    marketplace.showItemDetails(listingId);
}

function showPurchaseModal(listingId) {
    marketplace.showPurchaseModal(listingId);
}

function placeBid(listingId) {
    marketplace.placeBid(listingId);
}

function filterListings() {
    marketplace.filterListings();
}

function loadListings() {
    marketplace.loadListings();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    marketplace = new DOMPMarketplace();
});