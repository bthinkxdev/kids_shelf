// Kids Shelf - Cart Management

// Initialize cart from localStorage
function initCart() {
    const cart = localStorage.getItem('queenOrangeCart');
    return cart ? JSON.parse(cart) : [];
}

// Save cart to localStorage
function saveCart(cart) {
    localStorage.setItem('queenOrangeCart', JSON.stringify(cart));
    updateCartCount();
}

// Get cart
function getCart() {
    return initCart();
}

// Add to cart
function addToCart(productId, size, quantity = 1) {
    const product = getProductById(productId);
    if (!product) {
        alert('Product not found!');
        return false;
    }
    
    if (!size) {
        alert('Please select a size!');
        return false;
    }
    
    const cart = getCart();
    const existingItem = cart.find(item => item.id === productId && item.size === size);
    
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: productId,
            name: product.name,
            price: product.price,
            image: product.image,
            size: size,
            quantity: quantity,
            category: product.category
        });
    }
    
    saveCart(cart);
    return true;
}

// Remove from cart
function removeFromCart(productId, size) {
    let cart = getCart();
    cart = cart.filter(item => !(item.id === productId && item.size === size));
    saveCart(cart);
}

// Update quantity
function updateQuantity(productId, size, quantity) {
    const cart = getCart();
    const item = cart.find(item => item.id === productId && item.size === size);
    
    if (item) {
        if (quantity <= 0) {
            removeFromCart(productId, size);
        } else {
            item.quantity = quantity;
            saveCart(cart);
        }
    }
}

// Get cart total
function getCartTotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

// Get cart count
function getCartCount() {
    const cart = getCart();
    return cart.reduce((count, item) => count + item.quantity, 0);
}

// Clear cart
function clearCart() {
    localStorage.removeItem('queenOrangeCart');
    updateCartCount();
}

// Update cart count in header
function updateCartCount() {
    const count = getCartCount();
    const cartCountElements = document.querySelectorAll('.cart-count, .cart-badge');
    cartCountElements.forEach(element => {
        element.textContent = count;
        element.style.display = count > 0 ? 'flex' : 'none';
    });
}

// Generate WhatsApp message for cart
function generateWhatsAppMessage() {
    const cart = getCart();
    if (cart.length === 0) {
        return 'Hello Kids Shelf! I am interested in your products.';
    }
    
    let message = 'Hello Kids Shelf! I want to order:\n\n';
    cart.forEach((item, index) => {
        message += `${index + 1}. ${item.name}\n`;
        message += `   Size: ${item.size}\n`;
        message += `   Quantity: ${item.quantity}\n`;
        message += `   Price: ₹${item.price} x ${item.quantity} = ₹${item.price * item.quantity}\n\n`;
    });
    message += `Total: ₹${getCartTotal()}`;
    return encodeURIComponent(message);
}

// Generate WhatsApp link
function getWhatsAppLink(message = null, phone = '919876543210') {
    const finalMessage = message || generateWhatsAppMessage();
    return `https://wa.me/${phone}?text=${finalMessage}`;
}

