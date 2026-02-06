// Kids Shelf - UI JavaScript

document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initMobileSearch();
    initScrollEffects();
    initAnimations();
    initDjangoMessages();
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