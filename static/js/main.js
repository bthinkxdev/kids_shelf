// Kids Shelf - UI JavaScript

document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initMobileSearch();
    initScrollEffects();
    initAnimations();
    initDjangoMessages();
    initProductAddToCart(); 
    initCartPopup();        
});

function initMobileMenu() {
    const menuToggle = document.querySelector(".mobile-menu-toggle");
    const navMenu = document.querySelector(".nav-menu");

    if (!menuToggle || !navMenu) return;

    menuToggle.addEventListener("click", () => {
        navMenu.classList.toggle("active");
        menuToggle.classList.toggle("active");
        document.body.style.overflow = navMenu.classList.contains("active") ? "hidden" : "";
    });

    navMenu.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", () => {
            navMenu.classList.remove("active");
            menuToggle.classList.remove("active");
            document.body.style.overflow = "";
        });
    });

    document.addEventListener("click", (event) => {
        if (!menuToggle.contains(event.target) && !navMenu.contains(event.target)) {
            navMenu.classList.remove("active");
            menuToggle.classList.remove("active");
            document.body.style.overflow = "";
        }
    });
}

function initMobileSearch() {
    const searchToggle = document.getElementById("mobileSearchToggle");
    const searchOverlay = document.getElementById("mobileSearchOverlay");
    const searchClose = document.getElementById("mobileSearchClose");
    const searchInput = document.querySelector(".mobile-search-input");

    if (!searchToggle || !searchOverlay) return;

    // Open mobile search
    searchToggle.addEventListener("click", () => {
        searchOverlay.classList.add("active");
        document.body.style.overflow = "hidden";
        
        // Auto-focus search input after animation
        setTimeout(() => {
            if (searchInput) searchInput.focus();
        }, 300);
    });

    // Close mobile search
    const closeSearch = () => {
        searchOverlay.classList.remove("active");
        document.body.style.overflow = "";
        if (searchInput) searchInput.value = "";
    };

    if (searchClose) {
        searchClose.addEventListener("click", closeSearch);
    }

    // Close on overlay click (outside form)
    searchOverlay.addEventListener("click", (e) => {
        if (e.target === searchOverlay) {
            closeSearch();
        }
    });

    // Close on ESC key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && searchOverlay.classList.contains("active")) {
            closeSearch();
        }
    });
}

function initAnimations() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("fade-in");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    document.querySelectorAll(".product-card, .category-card").forEach((el) => {
        observer.observe(el);
    });
}

function initDjangoMessages() {
    const notifications = document.querySelectorAll('.notification');
    if (!notifications.length) return;
    
    notifications.forEach((notification) => {
        setTimeout(() => {
            notification.classList.remove('show');
            
            setTimeout(() => {
                notification.remove();
                
                const container = document.getElementById('notificationContainer');
                if (container && !container.querySelector('.notification')) {
                    container.remove();
                }
            }, 300);
        }, 3000);
    });
}

function initScrollEffects() {
    const header = document.querySelector(".header");
    if (!header) return;

    window.addEventListener("scroll", () => {
        header.classList.toggle("scrolled", window.scrollY > 100);
    });
}

function scrollBestsellers(direction) {
    const container = document.querySelector(".bestsellers-scroll-container");
    if (!container) return;
    const scrollAmount = 320;
    const next = direction === "left" ? container.scrollLeft - scrollAmount : container.scrollLeft + scrollAmount;
    container.scrollTo({ left: next, behavior: "smooth" });
}

function showNotification(message, type = "success") {
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        document.body.appendChild(container);
    }
    
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add("show");
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove("show");
        setTimeout(() => {
            notification.remove();
            
            if (!container.querySelector('.notification')) {
                container.remove();
            }
        }, 300);
    }, 3000);
}

function getCookie(name) {
    const cookieValue = document.cookie
        .split(";")
        .map((cookie) => cookie.trim())
        .find((cookie) => cookie.startsWith(`${name}=`));
    if (!cookieValue) return "";
    return decodeURIComponent(cookieValue.split("=")[1]);
}

function updateCartBadge(count) {
    const badges = document.querySelectorAll(".cart-badge");
    badges.forEach((badge) => {
        if (!count) {
            badge.remove();
            return;
        }
        badge.textContent = count;
        badge.style.display = "flex";
    });
    if (count && badges.length === 0) {
        const cartBtn = document.querySelector(".cart-btn");
        if (!cartBtn) return;
        const badge = document.createElement("span");
        badge.className = "cart-badge";
        badge.textContent = count;
        cartBtn.appendChild(badge);
    }
}
function updateWishlistBadge(count) {
    const wishlistBtn = document.querySelector('.wishlist-btn');
    if (!wishlistBtn) return;

    let badge = wishlistBtn.querySelector('.wishlist-badge');

    if (!count || count === 0) {
        if (badge) badge.remove();
        return;
    }

    if (!badge) {
        badge = document.createElement('span');
        badge.className = 'wishlist-badge';
        wishlistBtn.appendChild(badge);
    }

    badge.textContent = count;
}

// =============================================
// CART POPUP — on page load show if cart has items
// =============================================

function initCartPopup() {
    const popup = document.getElementById('cartPopup');
    if (!popup) return;
    const count = parseInt(popup.dataset.cartCount || '0', 10);
    if (count > 0) {
        const textEl = document.getElementById('cartPopupText');
        if (textEl) {
            textEl.textContent = count + ' item' + (count !== 1 ? 's' : '') + ' in your cart';
        }
        popup.classList.add('visible');
    }
}

let _cartPopupTimer = null;

function showCartPopup(cartCount) {
    const popup = document.getElementById('cartPopup');
    const textEl = document.getElementById('cartPopupText');
    if (!popup) return;

    if (_cartPopupTimer) {
        clearTimeout(_cartPopupTimer);
        _cartPopupTimer = null;
    }

    popup.classList.remove('cart-popup-warning');
    popup.dataset.cartCount = cartCount;

    if (textEl) {
        textEl.textContent = cartCount + ' item' + (cartCount !== 1 ? 's' : '') + ' in your cart';
    }

    popup.classList.add('visible');
}

function showAlreadyInCartPopup(cartCount) {
    const popup = document.getElementById('cartPopup');
    const textEl = document.getElementById('cartPopupText');
    if (!popup) return;

    if (_cartPopupTimer) {
        clearTimeout(_cartPopupTimer);
        _cartPopupTimer = null;
    }

    if (textEl) textEl.textContent = 'Already in your cart';
    popup.classList.add('visible', 'cart-popup-warning');

    // Revert to normal after 2s but keep bar visible
    _cartPopupTimer = setTimeout(function () {
        popup.classList.remove('cart-popup-warning');
        const count = parseInt(popup.dataset.cartCount || '0', 10);
        if (textEl && count > 0) {
            textEl.textContent = count + ' item' + (count !== 1 ? 's' : '') + ' in your cart';
        }
        _cartPopupTimer = null;
    }, 2000);
}

// =============================================
// ADD TO CART — AJAX (product detail page)
// =============================================

function initProductAddToCart() {
    const form = document.getElementById('addToCartForm');
    if (!form) return;

    let lastClickedAction = 'add';
    let isSubmitting = false;

    form.querySelectorAll('button[type="submit"]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            lastClickedAction = btn.value || 'add';
        });
    });

    form.addEventListener('submit', async function (e) {
        // Buy Now — normal redirect
        if (lastClickedAction === 'buy') return;

        e.preventDefault();

        if (isSubmitting) return;
        isSubmitting = true;

        const submitBtn = form.querySelector('button[value="add"]');
        const btnSpan = submitBtn ? submitBtn.querySelector('span') : null;
        const originalText = btnSpan ? btnSpan.textContent : (submitBtn ? submitBtn.textContent : '');

        if (submitBtn) {
            submitBtn.disabled = true;
            if (btnSpan) btnSpan.textContent = 'Adding...';
            else submitBtn.textContent = 'Adding...';
        }

        try {
            const formData = new FormData();
            formData.append('product_id', form.querySelector('[name="product_id"]').value);
            formData.append('format_type', form.querySelector('[name="format_type"]').value);
            formData.append('quantity', form.querySelector('[name="quantity"]').value);
            formData.append('action', lastClickedAction);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            const response = await fetch('/cart/add/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                showNotification(data.error || 'Could not add to cart.', 'error');
                return;
            }

            if (data.already_in_cart) {
                updateCartBadge(data.cart_count);
                showAlreadyInCartPopup(data.cart_count);
                return;
            }

            if (!data.success) {
                showNotification(data.error || 'Could not add to cart.', 'error');
                return;
            }

            // Success
            updateCartBadge(data.cart_count);
            showCartPopup(data.cart_count);

        } catch (err) {
            console.error('Add to cart error:', err);
            showNotification('Something went wrong. Please try again.', 'error');
        } finally {
            setTimeout(function () {
                isSubmitting = false;
                if (submitBtn) {
                    submitBtn.disabled = false;
                    if (btnSpan) btnSpan.textContent = originalText;
                    else submitBtn.textContent = originalText;
                }
            }, 1000);
        }
    });
}

// =============================================
// QUICK ADD TO CART (product listing cards)
// =============================================

function initQuickAddToCart() {
    const buttons = document.querySelectorAll(".js-add-to-cart");
    if (!buttons.length) return;
    buttons.forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            event.stopPropagation();
            const productId = button.dataset.productId;
            const size = button.dataset.size;
            const color = button.dataset.color || "";
            if (!productId || !size) {
                showNotification("Please select a size on the product page.", "error");
                return;
            }
            try {
                const formData = new FormData();
                formData.append("product_id", productId);
                formData.append("size", size);
                formData.append("color", color);
                formData.append("quantity", "1");
                const response = await fetch("/cart/add/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: formData,
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    showNotification(data.error || "Unable to add to cart.", "error");
                    return;
                }
                updateCartBadge(data.cart_count);
                showNotification("Added to cart!");
            } catch (error) {
                showNotification("Unable to add to cart.", "error");
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initQuickAddToCart();
});

(function() {
    var slider = document.getElementById('bannerSlider');
    if (!slider) return;
    var slides = slider.querySelectorAll('.banner-slide');
    var current = 0;
    function showSlide(idx) {
        slides.forEach(function(slide, i) {
            slide.classList.toggle('active', i === idx);
        });
    }
    setInterval(function() {
        current = (current + 1) % slides.length;
        showSlide(current);
    }, 3400);
})();

// Social FAB Toggle
const socialToggle = document.getElementById('socialToggle');
const socialMenu = document.getElementById('socialMenu');

if (socialToggle && socialMenu) {
    socialToggle.addEventListener('click', () => {
        socialToggle.classList.toggle('active');
        socialMenu.classList.toggle('active');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const notification = document.querySelector('.notification.error');
    
    if (notification) {
        showNotification(notification.textContent.trim(), 'error');
        notification.remove();
    }
});

function initWishlist() {
    // Load saved product IDs and mark hearts on page
    if (document.querySelector('.js-wishlist-toggle')) {
        fetch('/wishlist/ids/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.ok ? r.json() : { product_ids: [] })
        .then(data => {
            const ids = new Set((data.product_ids || []).map(String));
            document.querySelectorAll('.js-wishlist-toggle[data-product-id]').forEach(btn => {
                const pid = String(btn.dataset.productId);
                if (ids.has(pid)) {
                    btn.classList.add('in-wishlist');
                    const heart = btn.querySelector('.wishlist-heart, .wishlist-nav-icon');
                    if (heart) heart.setAttribute('fill', 'currentColor');
                }
            });
        })
        .catch(() => {});
    }

    // Handle clicks
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.js-wishlist-toggle');
        if (!btn) return;

        e.preventDefault();
        e.stopPropagation();

        const productId = btn.dataset.productId;
        if (!productId) return;

        fetch('/wishlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ product_id: parseInt(productId) }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.login_required) {
                window.location.href = data.login_url;
                return;
            }
            if (!data.success) {
                showNotification(data.error || 'Could not update wishlist.', 'error');
                return;
            }

            // Toggle all hearts with same product id (navbar + page button)
            document.querySelectorAll(`.js-wishlist-toggle[data-product-id="${productId}"]`).forEach(el => {
                el.classList.toggle('in-wishlist', data.added);
                const heart = el.querySelector('.wishlist-heart, .wishlist-nav-icon');
                if (heart) {
                    heart.setAttribute('fill', data.added ? 'currentColor' : 'none');
                }
                el.setAttribute('aria-label', data.added ? 'Remove from wishlist' : 'Add to wishlist');
            });

            // If on wishlist page, remove the card
            if (!data.added) {
                const card = btn.closest('.wishlist-item');
                if (card) {
                    card.style.transition = 'opacity 0.3s, transform 0.3s';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.9)';
                    setTimeout(() => card.remove(), 300);
                }
            }
            updateWishlistBadge(data.count);
            showNotification(data.added ? '❤️ Added to wishlist!' : 'Removed from wishlist.');
        })
        .catch(() => showNotification('Could not update wishlist.', 'error'));
    });
}

document.addEventListener('DOMContentLoaded', initWishlist);