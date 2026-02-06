// Kids Shelf - Product Data

const CATEGORIES = [
    { id: 'full-nighty', name: 'Full Nighty', slug: 'full-nighty', image: 'images/full_nighty.jpg' },
    { id: 'frock-nighty', name: 'Frock Nighty', slug: 'frock-nighty', image: 'images/froknighty.jpg' },
    { id: 'feeding-nighty', name: 'Feeding Nighty', slug: 'feeding-nighty', image: 'images/Feeding.jpg' },
    { id: 'pleated-nighty', name: 'Pleated Nighty', slug: 'pleated-nighty', image: 'images/Pleated.jpg' },
    { id: 'cord-set', name: 'Cord Set', slug: 'cord-set', image: 'images/Cord_set.jpg' },
    { id: 'churidar-3piece', name: 'Churidar 3 Piece Set', slug: 'churidar-3piece', image: 'images/Churidar_3_piece_set.jpg' },
    { id: '2piece-set', name: '2 Piece Set', slug: '2piece-set', image: 'images/2_piece_set.jpg' },
    { id: 'top', name: 'Top', slug: 'top', image: 'images/Top.jpg' },
    { id: 'short-top', name: 'Short Top', slug: 'short-top', image: 'images/Short_top.jpg' },
    { id: 'babies-dresses', name: 'Babies Dresses', slug: 'babies-dresses', image: 'images/Babies_dresses.jpg' }
];

const PRODUCTS = [
    // Full Nighty
    {
        id: 1,
        name: 'Elegant Cotton Full Nighty',
        category: 'full-nighty',
        price: 899,
        originalPrice: 1299,
        discount: 31,
        image: 'images/full_nighty.jpg',
        images: [
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg'
        ],
        colors: [
            { name: 'Pink', code: '#FFB6C1', available: true },
            { name: 'Blue', code: '#87CEEB', available: true },
            { name: 'Lavender', code: '#E6E6FA', available: true },
            { name: 'Peach', code: '#FFDAB9', available: false }
        ],
        sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        description: 'Premium cotton full-length nighty with elegant design. Perfect for comfortable night wear with soft fabric.',
        featured: true,
        bestseller: true
    },
    {
        id: 2,
        name: 'Floral Print Full Nighty',
        category: 'full-nighty',
        price: 749,
        originalPrice: 999,
        discount: 25,
        image: 'images/full_nighty.jpg',
        images: [
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg'
        ],
        colors: [
            { name: 'White', code: '#FFFFFF', available: true },
            { name: 'Cream', code: '#F5E6D3', available: true },
            { name: 'Light Blue', code: '#ADD8E6', available: true }
        ],
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Beautiful floral print full nighty with comfortable fit. Made from breathable fabric.',
        featured: false,
        bestseller: true
    },
    {
        id: 3,
        name: 'Silk Touch Full Nighty',
        category: 'full-nighty',
        price: 1199,
        originalPrice: 1599,
        discount: 25,
        image: 'images/full_nighty.jpg',
        images: [
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg',
            'images/full_nighty.jpg'
        ],
        colors: [
            { name: 'Burgundy', code: '#800020', available: true },
            { name: 'Navy', code: '#000080', available: true },
            { name: 'Emerald', code: '#50C878', available: true }
        ],
        sizes: ['M', 'L', 'XL', 'XXL'],
        description: 'Luxurious silk touch full nighty for a premium feel. Elegant design with lace details.',
        featured: true,
        bestseller: false
    },

    // Frock Nighty
    {
        id: 4,
        name: 'Princess Frock Nighty',
        category: 'frock-nighty',
        price: 849,
        originalPrice: 1199,
        discount: 29,
        image: 'images/froknighty.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Cute frock style nighty with flared bottom. Comfortable and stylish nightwear.',
        featured: true,
        bestseller: false
    },
    {
        id: 5,
        name: 'Lace Trim Frock Nighty',
        category: 'frock-nighty',
        price: 949,
        originalPrice: 1299,
        discount: 27,
        image: 'images/froknighty.jpg',
        sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        description: 'Beautiful frock nighty with delicate lace trim. Soft and comfortable fabric.',
        featured: false,
        bestseller: true
    },

    // Feeding Nighty
    {
        id: 6,
        name: 'Nursing Feeding Nighty',
        category: 'feeding-nighty',
        price: 799,
        originalPrice: 1099,
        discount: 27,
        image: 'images/Feeding.jpg',
        sizes: ['M', 'L', 'XL', 'XXL'],
        description: 'Specially designed feeding nighty for nursing mothers. Easy access and comfortable fit.',
        featured: true,
        bestseller: true
    },
    {
        id: 7,
        name: 'Maternity Feeding Nighty',
        category: 'feeding-nighty',
        price: 899,
        originalPrice: 1199,
        discount: 25,
        image: 'images/Feeding.jpg',
        sizes: ['L', 'XL', 'XXL'],
        description: 'Premium maternity feeding nighty with button closure. Soft cotton fabric.',
        featured: false,
        bestseller: true
    },
    {
        id: 8,
        name: 'Zip Front Feeding Nighty',
        category: 'feeding-nighty',
        price: 849,
        originalPrice: 1149,
        discount: 26,
        image: 'images/Feeding.jpg',
        sizes: ['M', 'L', 'XL'],
        description: 'Convenient zip front feeding nighty. Perfect for new mothers.',
        featured: false,
        bestseller: false
    },

    // Pleated Nighty
    {
        id: 9,
        name: 'Elegant Pleated Nighty',
        category: 'pleated-nighty',
        price: 1099,
        originalPrice: 1499,
        discount: 27,
        image: 'images/Pleated.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Stylish pleated nighty with flowing design. Premium quality fabric.',
        featured: true,
        bestseller: false
    },
    {
        id: 10,
        name: 'Box Pleated Nighty',
        category: 'pleated-nighty',
        price: 999,
        originalPrice: 1399,
        discount: 29,
        image: 'images/Pleated.jpg',
        sizes: ['M', 'L', 'XL', 'XXL'],
        description: 'Beautiful box pleated design nighty. Comfortable and elegant.',
        featured: false,
        bestseller: false
    },

    // Cord Set
    {
        id: 11,
        name: 'Summer Cord Set',
        category: 'cord-set',
        price: 1299,
        originalPrice: 1799,
        discount: 28,
        image: 'images/Cord_set.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Trendy cord set with matching top and bottom. Perfect for loungewear.',
        featured: true,
        bestseller: true
    },
    {
        id: 12,
        name: 'Printed Cord Set',
        category: 'cord-set',
        price: 1199,
        originalPrice: 1599,
        discount: 25,
        image: 'images/Cord_set.jpg',
        sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        description: 'Stylish printed cord set with comfortable fit. Modern design.',
        featured: false,
        bestseller: true
    },
    {
        id: 13,
        name: 'Premium Cord Set',
        category: 'cord-set',
        price: 1499,
        originalPrice: 1999,
        discount: 25,
        image: 'images/Cord_set.jpg',
        sizes: ['M', 'L', 'XL'],
        description: 'Premium quality cord set with elegant design. Soft and breathable fabric.',
        featured: true,
        bestseller: false
    },

    // Churidar 3 Piece Set
    {
        id: 14,
        name: 'Traditional Churidar Set',
        category: 'churidar-3piece',
        price: 1599,
        originalPrice: 2199,
        discount: 27,
        image: 'images/Churidar_3_piece_set.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Complete 3 piece churidar set with dupatta. Beautiful traditional design.',
        featured: true,
        bestseller: true
    },
    {
        id: 15,
        name: 'Embroidered Churidar Set',
        category: 'churidar-3piece',
        price: 1799,
        originalPrice: 2399,
        discount: 25,
        image: 'images/Churidar_3_piece_set.jpg',
        sizes: ['M', 'L', 'XL', 'XXL'],
        description: 'Elegant embroidered churidar 3 piece set. Perfect for occasions.',
        featured: false,
        bestseller: true
    },

    // 2 Piece Set
    {
        id: 16,
        name: 'Casual 2 Piece Set',
        category: '2piece-set',
        price: 999,
        originalPrice: 1399,
        discount: 29,
        image: 'images/2_piece_set.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Comfortable 2 piece set for daily wear. Soft cotton blend.',
        featured: true,
        bestseller: false
    },
    {
        id: 17,
        name: 'Night 2 Piece Set',
        category: '2piece-set',
        price: 899,
        originalPrice: 1199,
        discount: 25,
        image: 'images/2_piece_set.jpg',
        sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        description: 'Cozy 2 piece night set. Perfect for comfortable sleep.',
        featured: false,
        bestseller: true
    },
    {
        id: 18,
        name: 'Premium 2 Piece Set',
        category: '2piece-set',
        price: 1199,
        originalPrice: 1599,
        discount: 25,
        image: 'images/2_piece_set.jpg',
        sizes: ['M', 'L', 'XL'],
        description: 'Premium quality 2 piece lounge set. Stylish and comfortable.',
        featured: false,
        bestseller: false
    },

    // Top
    {
        id: 19,
        name: 'Casual Cotton Top',
        category: 'top',
        price: 499,
        originalPrice: 699,
        discount: 29,
        image: 'images/Top.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Comfortable cotton top for everyday wear. Breathable fabric.',
        featured: true,
        bestseller: true
    },
    {
        id: 20,
        name: 'Printed Fashion Top',
        category: 'top',
        price: 599,
        originalPrice: 799,
        discount: 25,
        image: 'images/Top.jpg',
        sizes: ['S', 'M', 'L', 'XL', 'XXL'],
        description: 'Trendy printed top with modern design. Comfortable fit.',
        featured: false,
        bestseller: true
    },
    {
        id: 21,
        name: 'Designer Top',
        category: 'top',
        price: 749,
        originalPrice: 999,
        discount: 25,
        image: 'images/Top.jpg',
        sizes: ['M', 'L', 'XL'],
        description: 'Designer top with elegant styling. Premium quality fabric.',
        featured: true,
        bestseller: false
    },

    // Short Top
    {
        id: 22,
        name: 'Summer Short Top',
        category: 'short-top',
        price: 449,
        originalPrice: 649,
        discount: 31,
        image: 'images/Short_top.jpg',
        sizes: ['S', 'M', 'L', 'XL'],
        description: 'Breezy short top perfect for summer. Light and comfortable.',
        featured: true,
        bestseller: true
    },
    {
        id: 23,
        name: 'Crop Short Top',
        category: 'short-top',
        price: 399,
        originalPrice: 599,
        discount: 33,
        image: 'images/Short_top.jpg',
        sizes: ['S', 'M', 'L'],
        description: 'Stylish crop short top. Modern and trendy design.',
        featured: false,
        bestseller: true
    },

    // Babies Dresses
    {
        id: 24,
        name: 'Baby Girl Frock',
        category: 'babies-dresses',
        price: 599,
        originalPrice: 799,
        discount: 25,
        image: 'images/Babies_dresses.jpg',
        sizes: ['6M', '12M', '18M', '24M'],
        description: 'Adorable baby girl frock with cute design. Soft cotton fabric.',
        featured: true,
        bestseller: true
    },
    {
        id: 25,
        name: 'Infant Party Dress',
        category: 'babies-dresses',
        price: 699,
        originalPrice: 949,
        discount: 26,
        image: 'images/Babies_dresses.jpg',
        sizes: ['6M', '12M', '18M'],
        description: 'Beautiful party dress for infants. Perfect for special occasions.',
        featured: false,
        bestseller: true
    },
    {
        id: 26,
        name: 'Baby Casual Dress',
        category: 'babies-dresses',
        price: 499,
        originalPrice: 699,
        discount: 29,
        image: 'images/Babies_dresses.jpg',
        sizes: ['12M', '18M', '24M'],
        description: 'Comfortable casual dress for babies. Easy to wear.',
        featured: true,
        bestseller: false
    },
    {
        id: 27,
        name: 'Toddler Frock',
        category: 'babies-dresses',
        price: 649,
        originalPrice: 899,
        discount: 28,
        image: 'images/Babies_dresses.jpg',
        sizes: ['18M', '24M', '3Y'],
        description: 'Pretty toddler frock with vibrant colors. Soft and comfortable.',
        featured: false,
        bestseller: true
    }
];

// Get product by ID
function getProductById(id) {
    return PRODUCTS.find(p => p.id === parseInt(id));
}

// Get products by category
function getProductsByCategory(categorySlug) {
    if (!categorySlug) return PRODUCTS;
    return PRODUCTS.filter(p => p.category === categorySlug);
}

// Get featured products
function getFeaturedProducts() {
    return PRODUCTS.filter(p => p.featured);
}

// Get bestseller products
function getBestsellerProducts() {
    return PRODUCTS.filter(p => p.bestseller);
}

// Get related products (same category, different product)
function getRelatedProducts(productId, categorySlug, limit = 4) {
    return PRODUCTS
        .filter(p => p.category === categorySlug && p.id !== parseInt(productId))
        .slice(0, limit);
}

// Filter products
function filterProducts(category, minPrice, maxPrice, size) {
    let filtered = PRODUCTS;
    
    if (category && category !== 'all') {
        filtered = filtered.filter(p => p.category === category);
    }
    
    if (minPrice) {
        filtered = filtered.filter(p => p.price >= parseInt(minPrice));
    }
    
    if (maxPrice) {
        filtered = filtered.filter(p => p.price <= parseInt(maxPrice));
    }
    
    if (size) {
        filtered = filtered.filter(p => p.sizes.includes(size));
    }
    
    return filtered;
}

// Get product images (returns array of images or creates default from single image)
function getProductImages(product) {
    if (product.images && product.images.length > 0) {
        return product.images;
    }
    // Default: create 3 copies of the main image
    return [product.image, product.image, product.image];
}

// Get product colors (returns array of colors or creates defaults)
function getProductColors(product) {
    if (product.colors && product.colors.length > 0) {
        return product.colors;
    }
    // Default colors for clothing
    return [
        { name: 'Pink', code: '#FFB6C1', available: true },
        { name: 'Blue', code: '#87CEEB', available: true },
        { name: 'White', code: '#FFFFFF', available: true },
        { name: 'Peach', code: '#FFDAB9', available: true }
    ];
}

