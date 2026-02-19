from django import forms
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.models import User
import re
from .models import Address, ContactMessage, NewsletterSubscription


class CartAddForm(forms.Form):
    product_id = forms.IntegerField(min_value=1)
    format_type = forms.CharField(max_length=20)
    quantity = forms.IntegerField(min_value=1)


class CartUpdateForm(forms.Form):
    item_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=0)


class CheckoutForm(forms.Form):
    # Address selection
    selected_address = forms.IntegerField(required=False, widget=forms.HiddenInput())
    use_new_address = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())
    
    # Contact and address fields
    full_name = forms.CharField(max_length=120, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    address_line = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Address")
    city = forms.CharField(max_length=80, required=False)
    state = forms.CharField(max_length=80, required=False)
    pincode = forms.CharField(max_length=10, required=False)
    
    # Payment
    payment = forms.ChoiceField(
        choices=[("cod", "Cash on Delivery"), ("whatsapp", "WhatsApp Order"), ("razorpay", "Online Payment")],
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields["payment"].initial = "cod"
        for field in self.fields.values():
            if isinstance(field.widget, (forms.RadioSelect, forms.HiddenInput)):
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-input".strip()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not re.match(r'^\+?[\d\s\-]{7,15}$', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and not re.match(r'^\d{6}$', pincode):
            raise forms.ValidationError('Enter a valid 6-digit PIN code.')
        return pincode

    def clean(self):
        cleaned_data = super().clean()
        selected_address = cleaned_data.get('selected_address')
        use_new_address = cleaned_data.get('use_new_address')
        is_guest = not self.user

        # Guest: must use new address; email required
        if is_guest:
            use_new_address = True
            cleaned_data['use_new_address'] = True
            cleaned_data['selected_address'] = None
            if not cleaned_data.get('email'):
                self.add_error('email', 'Email is required for checkout.')
            required_fields = ['full_name', 'phone', 'email', 'address_line', 'city', 'state', 'pincode']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required.')
            return cleaned_data

        # Authenticated: existing or new address
        if selected_address and not use_new_address:
            try:
                address = Address.objects.get(pk=selected_address, user=self.user, is_snapshot=False)
                cleaned_data['full_name'] = address.full_name
                cleaned_data['phone'] = address.phone
                cleaned_data['email'] = address.email
                cleaned_data['address_line'] = address.address_line
                cleaned_data['city'] = address.city
                cleaned_data['state'] = address.state
                cleaned_data['pincode'] = address.pincode
            except Address.DoesNotExist:
                raise forms.ValidationError("Selected address not found.")
        else:
            if not use_new_address and not selected_address:
                if Address.objects.filter(user=self.user, is_snapshot=False).exists():
                    raise forms.ValidationError("Please select an address or add a new one.")
                else:
                    use_new_address = True
                    cleaned_data['use_new_address'] = True

            if use_new_address:
                required_fields = ['full_name', 'phone', 'address_line', 'city', 'state', 'pincode']
                for field in required_fields:
                    if not cleaned_data.get(field):
                        self.add_error(field, 'This field is required.')

        return cleaned_data

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-input".strip()


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ["email"]


class EmailOTPRequestForm(forms.Form):
    """Form for requesting OTP via email"""
    email = forms.EmailField(
        max_length=254,
        required=True,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        return email


class OTPVerificationForm(forms.Form):
    """Form for verifying OTP"""
    email = forms.EmailField(widget=forms.HiddenInput())
    otp = forms.CharField(
        max_length=4,
        min_length=4,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\d{4}$',
                message='OTP must be exactly 4 digits',
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input otp-input',
            'placeholder': '0000',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
        })
    )
    
    def clean_otp(self):
        otp = self.cleaned_data.get('otp', '').strip()
        if not otp.isdigit():
            raise forms.ValidationError('OTP must contain only digits')
        return otp


class UserProfileForm(forms.Form):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last Name',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone Number',
        })
    )


class AddressForm(forms.ModelForm):
    """Form for adding/editing shipping addresses"""
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line', 'city', 'state', 'pincode', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Full Name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number',
            }),
            'address_line': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Street Address',
                'rows': 3,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'State',
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'PIN Code',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

class ReviewForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        error_messages={
            "required": "Please select a rating.",
            "min_value": "Rating must be at least 1 star.",
            "max_value": "Rating cannot exceed 5 stars.",
        },
    )
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Summary of your review (optional)",
            "id": "id_title",
        }),
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Share your experience with this book...",
            "rows": 4,
            "id": "id_comment",
        }),
    )