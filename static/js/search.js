// Navbar Search functionality
function performSearch(event) {
    const query = event.target.value.toLowerCase().trim();
    const resultsContainer = document.getElementById('navbarSearchResults');
    
    if (!resultsContainer) return;
    
    if (query.length === 0) {
        resultsContainer.innerHTML = '';
        resultsContainer.classList.remove('active');
        return;
    }
    
    if (query.length < 2) {
        resultsContainer.innerHTML = '<div class="search-message" style="padding: var(--space-4); text-align: center; color: var(--gray-500); font-size: 14px;">Type at least 2 characters...</div>';
        resultsContainer.classList.add('active');
        return;
    }
    
    // Search through all products
    const results = PRODUCTS.filter(product => 
        product.name.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query) ||
        (product.description && product.description.toLowerCase().includes(query))
    );
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="search-message" style="padding: var(--space-6); text-align: center; color: var(--gray-600); font-size: 15px;">No products found matching "' + query + '"</div>';
        resultsContainer.classList.add('active');
        return;
    }
    
    // Display results
    let html = '<div style="padding: var(--space-5);">';
    html += '<div style="font-size: 12px; font-weight: 700; color: var(--primary-dark); margin-bottom: var(--space-4); text-transform: uppercase; letter-spacing: 1px;">Found ' + results.length + ' product(s)</div>';
    html += '<div style="display: grid; gap: var(--space-2);">';
    
    results.slice(0, 5).forEach(product => {
        html += `
            <a href="product.html?id=${product.id}" class="navbar-search-result-item" style="display: flex; gap: var(--space-3); padding: var(--space-3); border-radius: 12px; transition: all 0.2s ease; text-decoration: none; color: inherit;">
                <div style="width: 60px; height: 75px; flex-shrink: 0; border-radius: 8px; overflow: hidden; background: var(--gray-100);">
                    <img src="${product.image}" alt="${product.name}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 4px;">
                    <div style="font-size: 10px; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;">${product.category}</div>
                    <div style="font-size: 14px; font-weight: 600; color: var(--black); line-height: 1.3;">${product.name}</div>
                    <div style="font-size: 16px; font-weight: 800; color: var(--primary-dark);">₹${product.price}</div>
                </div>
            </a>
        `;
    });
    
    html += '</div>';
    
    if (results.length > 5) {
        html += '<div style="margin-top: var(--space-4); padding-top: var(--space-4); border-top: 1px solid var(--gray-200); text-align: center;"><a href="category.html?search=' + encodeURIComponent(query) + '" class="btn btn-primary" style="padding: var(--space-3) var(--space-6); font-size: 13px;">View All ' + results.length + ' Results</a></div>';
    }
    
    html += '</div>';
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.add('active');
    
    // Add hover effects
    setTimeout(() => {
        const items = resultsContainer.querySelectorAll('.navbar-search-result-item');
        items.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.background = 'var(--cream)';
                this.style.transform = 'translateX(4px)';
            });
            item.addEventListener('mouseleave', function() {
                this.style.background = 'transparent';
                this.style.transform = 'translateX(0)';
            });
        });
    }, 0);
}

// Toggle Mobile Inline Search
function toggleSearchOverlay() {
    // Check if we're on mobile
    if (window.innerWidth >= 1025) {
        return; // Do nothing on desktop
    }
    
    const navbarSearch = document.querySelector('.navbar-search');
    const navWrapper = document.querySelector('.nav-wrapper');
    const navbarSearchInput = document.getElementById('navbarSearchInput');
    const resultsContainer = document.getElementById('navbarSearchResults');
    
    if (!navbarSearch || !navWrapper) return;
    
    const isActive = navbarSearch.classList.contains('mobile-search-active');
    
    if (isActive) {
        // Close search
        navbarSearch.classList.remove('mobile-search-active');
        navWrapper.classList.remove('search-active');
        navbarSearchInput.value = '';
        if (resultsContainer) {
            resultsContainer.classList.remove('active');
            resultsContainer.innerHTML = '';
        }
    } else {
        // Open search
        navbarSearch.classList.add('mobile-search-active');
        navWrapper.classList.add('search-active');
        setTimeout(() => {
            navbarSearchInput.focus();
        }, 100);
    }
}


// Handle Enter key in navbar search
document.addEventListener('DOMContentLoaded', function() {
    const navbarSearchInput = document.getElementById('navbarSearchInput');
    if (navbarSearchInput) {
        navbarSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query.length >= 2) {
                    window.location.href = 'category.html?search=' + encodeURIComponent(query);
                }
            }
        });
        
        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            const navbarSearch = document.querySelector('.navbar-search');
            const resultsContainer = document.getElementById('navbarSearchResults');
            
            if (navbarSearch && !navbarSearch.contains(e.target)) {
                if (resultsContainer) {
                    resultsContainer.classList.remove('active');
                }
            }
        });
    }
    
    // Close mobile search on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const navbarSearch = document.querySelector('.navbar-search');
            if (navbarSearch && navbarSearch.classList.contains('mobile-search-active')) {
                toggleSearchOverlay();
            }
        }
    });
    
    // Close mobile search when clicking outside
    document.addEventListener('click', function(e) {
        const navbarSearch = document.querySelector('.navbar-search');
        const searchBtn = document.querySelector('.search-btn');
        
        if (navbarSearch && navbarSearch.classList.contains('mobile-search-active')) {
            if (!navbarSearch.contains(e.target) && !searchBtn.contains(e.target)) {
                toggleSearchOverlay();
            }
        }
    });
});
