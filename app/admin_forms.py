from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet

from .models import Category, Product, ProductImage, BookFormat, AgeGroup


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
            "autocomplete": "username"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
            "autocomplete": "current-password"
        })
    )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "is_active", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category Name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "category-slug"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if image.size > max_size:
                raise forms.ValidationError(f'Image file size cannot exceed 5MB. Current size: {image.size / (1024 * 1024):.2f}MB')
            
            # Check pixel count (5MP)
            try:
                from PIL import Image
                img = Image.open(image)
                width, height = img.size
                if width * height > 5_000_000:
                    raise forms.ValidationError(
                        f'Image resolution cannot exceed 5 megapixels (5,000,000 pixels).\n'
                        f'Selected image: {getattr(image, "name", "uploaded file")}\n'
                        f'Resolution: {width} x {height} = {width * height:,} pixels.\n'
                        'Please choose a smaller image or resize/compress it before uploading.'
                    )
                img.verify()
                # Reset file pointer after verification
                image.seek(0)
            except forms.ValidationError:
                raise
            except Exception:
                raise forms.ValidationError('Invalid image file. Please upload a valid image (JPG, PNG, GIF, WebP).')
        
        return image


class ProductForm(forms.ModelForm):
    age_groups = forms.ModelMultipleChoiceField(
        queryset=None,  
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all applicable age groups (e.g., for ages 0-8, select 0-2, 3-5, and 6-8). Leave empty for 'All Ages'."
    )
    
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "slug",
            "description",
            "author",
            "illustrator",
            "publisher",
            "publication_year",
            "isbn",
            "age_groups",  
            "page_count",
            "language",
            "price",
            "original_price",  
            "is_featured",
            "is_bestseller",
            "is_active",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Book Title"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "book-slug"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Book Description"}),
            "author": forms.TextInput(attrs={"class": "form-control", "placeholder": "Author Name"}),
            "illustrator": forms.TextInput(attrs={"class": "form-control", "placeholder": "Illustrator (optional)"}),
            "publisher": forms.TextInput(attrs={"class": "form-control", "placeholder": "Publisher"}),
            "publication_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "2024", "min": "1900", "max": "2030"}),
            "isbn": forms.TextInput(attrs={"class": "form-control", "placeholder": "ISBN-13"}),
            "page_count": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Number of pages", "min": "1"}),
            "language": forms.TextInput(attrs={"class": "form-control", "placeholder": "English"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Sale Price", "step": "0.01", "min": "0"}),
            "original_price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Original MRP (optional)", "step": "0.01", "min": "0"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_bestseller": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            'original_price': 'MRP/Original price for showing discounts. Leave empty if not applicable.',
            'price': 'Current selling price (required)',
            'isbn': 'International Standard Book Number (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False        
        self.fields["age_groups"].queryset = AgeGroup.objects.filter(is_active=True).order_by('display_order')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "is_primary", "alt_text"]
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "alt_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Alt text"}),
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if image.size > max_size:
                raise forms.ValidationError(f'Image file size cannot exceed 5MB. Current size: {image.size / (1024 * 1024):.2f}MB')
            
            # Check pixel count (5MP)
            try:
                from PIL import Image
                img = Image.open(image)
                width, height = img.size
                if width * height > 5_000_000:
                    raise forms.ValidationError(
                        f'Image resolution cannot exceed 5 megapixels (5,000,000 pixels).\n'
                        f'Selected image: {getattr(image, "name", "uploaded file")}\n'
                        f'Resolution: {width} x {height} = {width * height:,} pixels.\n'
                        'Please choose a smaller image or resize/compress it before uploading.'
                    )
                img.verify()
                # Reset file pointer after verification
                image.seek(0)
            except forms.ValidationError:
                raise
            except Exception:
                raise forms.ValidationError('Invalid image file. Please upload a valid image (JPG, PNG, GIF, WebP).')
        
        return image

class ProductImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        image_count = sum(1 for form in self.forms 
                         if form.cleaned_data and not form.cleaned_data.get('DELETE', False) 
                         and (form.cleaned_data.get('image') or (form.instance and form.instance.pk)))
        if image_count == 0:
            raise forms.ValidationError('⚠️ At least one product image is required.')


class BookFormatInlineFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        skus = []
        format_types = []
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                sku = form.cleaned_data.get('sku')
                format_type = form.cleaned_data.get('format_type')
                
                if sku:
                    if sku in skus:
                        raise forms.ValidationError(f'❌ Duplicate SKU: "{sku}". Please change one.')
                    skus.append(sku)
                    
                    existing = BookFormat.objects.filter(sku=sku)
                    if self.instance and self.instance.pk:
                        existing = existing.exclude(product=self.instance)
                    if existing.exists():
                        raise forms.ValidationError(f'❌ SKU "{sku}" already used in "{existing.first().product.name}".')
                
                if format_type:
                    if format_type in format_types:
                        raise forms.ValidationError(f'❌ Duplicate format: {dict(BookFormat._meta.get_field("format_type").choices)[format_type]}')
                    format_types.append(format_type)

ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, formset=ProductImageInlineFormSet,
    extra=3, can_delete=True, max_num=5, validate_max=True,
)

class BookFormatForm(forms.ModelForm):
    class Meta:
        model = BookFormat
        fields = ["sku", "format_type", "stock_quantity", "is_active"]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "SKU (e.g., ISBN-HB)"}),
            "format_type": forms.Select(attrs={"class": "form-control"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

BookFormatFormSet = inlineformset_factory(
    Product, BookFormat, form=BookFormatForm, formset=BookFormatInlineFormSet,
    extra=2, can_delete=True, max_num=4,
)
