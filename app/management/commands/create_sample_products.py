from django.core.management.base import BaseCommand
from django.utils.text import slugify
from app.models import Category, AgeGroup, Product, ProductImage, BookFormat
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create 10 sample kids books in the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to create sample products...'))
        
        # Create or get categories
        categories_data = [
            {'name': 'Picture Books', 'slug': 'picture-books'},
            {'name': 'Early Readers', 'slug': 'early-readers'},
            {'name': 'Chapter Books', 'slug': 'chapter-books'},
            {'name': 'Board Books', 'slug': 'board-books'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name'], 'is_active': True}
            )
            categories[cat_data['slug']] = cat
            if created:
                self.stdout.write(f"[+] Created category: {cat.name}")
            else:
                self.stdout.write(f"[>] Category exists: {cat.name}")
        
        # Create or get age groups
        age_groups_data = [
            {'name': '0-2 Years', 'slug': '0-2-years', 'emoji': '👶', 'order': 1},
            {'name': '3-5 Years', 'slug': '3-5-years', 'emoji': '🧒', 'order': 2},
            {'name': '6-8 Years', 'slug': '6-8-years', 'emoji': '👦', 'order': 3},
            {'name': '9-12 Years', 'slug': '9-12-years', 'emoji': '🧑', 'order': 4},
        ]
        
        age_groups = {}
        for ag_data in age_groups_data:
            ag, created = AgeGroup.objects.get_or_create(
                slug=ag_data['slug'],
                defaults={
                    'name': ag_data['name'],
                    'emoji': ag_data['emoji'],
                    'display_order': ag_data['order'],
                    'is_active': True
                }
            )
            age_groups[ag_data['slug']] = ag
            if created:
                self.stdout.write(f"[+] Created age group: {ag.name}")
            else:
                self.stdout.write(f"[>] Age group exists: {ag.name}")
        
        # Sample books data
        books_data = [
            {
                'name': 'The Very Hungry Caterpillar',
                'author': 'Eric Carle',
                'category': 'picture-books',
                'age_groups': ['0-2-years', '3-5-years'],
                'description': 'A classic tale of a caterpillar eating his way through a variety of foods before transforming into a beautiful butterfly.',
                'price': Decimal('299.00'),
                'original_price': Decimal('399.00'),
                'publisher': 'Penguin',
                'publication_year': 1969,
                'page_count': 26,
                'isbn': '9780399226908',
                'is_featured': True,
                'is_bestseller': True,
            },
            {
                'name': 'Where the Wild Things Are',
                'author': 'Maurice Sendak',
                'category': 'picture-books',
                'age_groups': ['3-5-years', '6-8-years'],
                'description': 'The story of Max, who sails away to an island inhabited by wild creatures.',
                'price': Decimal('350.00'),
                'original_price': Decimal('450.00'),
                'publisher': 'HarperCollins',
                'publication_year': 1963,
                'page_count': 48,
                'isbn': '9780064431781',
                'is_featured': True,
                'is_bestseller': True,
            },
            {
                'name': 'The Gruffalo',
                'author': 'Julia Donaldson',
                'illustrator': 'Axel Scheffler',
                'category': 'picture-books',
                'age_groups': ['3-5-years', '6-8-years'],
                'description': 'A mouse takes a walk through the woods and encounters several dangerous animals.',
                'price': Decimal('275.00'),
                'original_price': Decimal('350.00'),
                'publisher': 'Macmillan',
                'publication_year': 1999,
                'page_count': 32,
                'isbn': '9780333710937',
                'is_bestseller': True,
            },
            {
                'name': 'Goodnight Moon',
                'author': 'Margaret Wise Brown',
                'illustrator': 'Clement Hurd',
                'category': 'board-books',
                'age_groups': ['0-2-years'],
                'description': 'A classic bedtime story featuring a bunny saying goodnight to everything around.',
                'price': Decimal('199.00'),
                'original_price': Decimal('250.00'),
                'publisher': 'HarperCollins',
                'publication_year': 1947,
                'page_count': 32,
                'isbn': '9780064430173',
                'is_featured': True,
            },
            {
                'name': 'Diary of a Wimpy Kid',
                'author': 'Jeff Kinney',
                'category': 'chapter-books',
                'age_groups': ['9-12-years'],
                'description': 'The hilarious journal of Greg Heffley navigating middle school.',
                'price': Decimal('399.00'),
                'original_price': Decimal('499.00'),
                'publisher': 'Amulet Books',
                'publication_year': 2007,
                'page_count': 224,
                'isbn': '9780810993136',
                'is_bestseller': True,
            },
            {
                'name': 'Charlotte\'s Web',
                'author': 'E.B. White',
                'category': 'chapter-books',
                'age_groups': ['6-8-years', '9-12-years'],
                'description': 'The story of a pig named Wilbur and his friendship with a barn spider named Charlotte.',
                'price': Decimal('325.00'),
                'original_price': Decimal('425.00'),
                'publisher': 'HarperCollins',
                'publication_year': 1952,
                'page_count': 192,
                'isbn': '9780064400558',
                'is_featured': True,
            },
            {
                'name': 'The Cat in the Hat',
                'author': 'Dr. Seuss',
                'category': 'early-readers',
                'age_groups': ['3-5-years', '6-8-years'],
                'description': 'On a rainy day, a tall cat brings chaos and fun to two bored children.',
                'price': Decimal('250.00'),
                'original_price': Decimal('325.00'),
                'publisher': 'Random House',
                'publication_year': 1957,
                'page_count': 61,
                'isbn': '9780394800011',
                'is_bestseller': True,
            },
            {
                'name': 'Brown Bear, Brown Bear, What Do You See?',
                'author': 'Bill Martin Jr.',
                'illustrator': 'Eric Carle',
                'category': 'board-books',
                'age_groups': ['0-2-years', '3-5-years'],
                'description': 'A rhythmic story featuring colorful animals and repetitive text perfect for young readers.',
                'price': Decimal('225.00'),
                'original_price': Decimal('299.00'),
                'publisher': 'Henry Holt',
                'publication_year': 1967,
                'page_count': 28,
                'isbn': '9780805047905',
                'is_featured': True,
            },
            {
                'name': 'Matilda',
                'author': 'Roald Dahl',
                'illustrator': 'Quentin Blake',
                'category': 'chapter-books',
                'age_groups': ['9-12-years'],
                'description': 'The story of an extraordinary girl with telekinetic powers and a love of books.',
                'price': Decimal('375.00'),
                'original_price': Decimal('475.00'),
                'publisher': 'Puffin Books',
                'publication_year': 1988,
                'page_count': 240,
                'isbn': '9780142410370',
                'is_bestseller': True,
            },
            {
                'name': 'Green Eggs and Ham',
                'author': 'Dr. Seuss',
                'category': 'early-readers',
                'age_groups': ['3-5-years', '6-8-years'],
                'description': 'Sam-I-Am tries to convince a grumpy friend to try green eggs and ham.',
                'price': Decimal('240.00'),
                'original_price': Decimal('310.00'),
                'publisher': 'Random House',
                'publication_year': 1960,
                'page_count': 62,
                'isbn': '9780394800165',
                'is_featured': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for book_data in books_data:
            # Extract age groups and category
            age_group_slugs = book_data.pop('age_groups')
            category_slug = book_data.pop('category')
            
            # Get or create product
            slug = slugify(book_data['name'])
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    **book_data,
                    'category': categories[category_slug],
                    'is_active': True,
                }
            )
            
            if created:
                # Add age groups (many-to-many)
                for ag_slug in age_group_slugs:
                    product.age_groups.add(age_groups[ag_slug])
                
                # Create book formats
                formats = [
                    {'format_type': 'paperback', 'stock': 15},
                    {'format_type': 'hardcover', 'stock': 10},
                ]
                
                for fmt in formats:
                    sku = f"{slug}-{fmt['format_type']}"[:64]
                    BookFormat.objects.create(
                        product=product,
                        format_type=fmt['format_type'],
                        sku=sku,
                        stock_quantity=fmt['stock'],
                        is_active=True
                    )
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[+] Created: {product.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"[>] Already exists: {product.name}"))
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"Summary:"))
        self.stdout.write(self.style.SUCCESS(f"  - Categories: {len(categories)}"))
        self.stdout.write(self.style.SUCCESS(f"  - Age Groups: {len(age_groups)}"))
        self.stdout.write(self.style.SUCCESS(f"  - New Products: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  - Existing Products: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"  - Total Products in DB: {Product.objects.count()}"))
        self.stdout.write("="*60 + "\n")
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Sample products created successfully!'))
            self.stdout.write(self.style.WARNING('\nNote: Product images need to be uploaded manually via admin panel.'))
        else:
            self.stdout.write(self.style.WARNING('All products already exist in the database.'))
