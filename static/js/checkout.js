/**
 * Checkout Page JavaScript
 * Handles address selection, payment method, and form interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initAddressSelection();
    initPaymentSelection();
    initAddressToggle();
});

// Address Selection
function initAddressSelection() {
    const addressRadios = document.querySelectorAll('input[name="address_selection"]');
    const selectedAddressInput = document.getElementById('id_selected_address');
    const useNewAddressInput = document.getElementById('id_use_new_address');
    const savedAddresses = document.getElementById('savedAddresses');

    if (!addressRadios.length) return;

    addressRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            // Remove selected class from all
            document.querySelectorAll('.address-card.selectable').forEach(card => {
                card.classList.remove('selected');
            });

            // Add selected class to chosen
            this.closest('.address-card').classList.add('selected');

            // Update hidden inputs
            if (selectedAddressInput) {
                selectedAddressInput.value = this.value;
            }
            if (useNewAddressInput) {
                useNewAddressInput.value = 'false';
            }
        });
    });
}

// Payment Method Selection
function initPaymentSelection() {
    const paymentRadios = document.querySelectorAll('.payment-option input[type="radio"]');

    // Set initial selected state on page load
    paymentRadios.forEach(radio => {
        if (radio.checked) {
            radio.closest('.payment-option').classList.add('selected');
        }
        
        radio.addEventListener('change', function() {
            // Remove selected class from all
            document.querySelectorAll('.payment-option').forEach(option => {
                option.classList.remove('selected');
            });

            // Add selected class to chosen
            this.closest('.payment-option').classList.add('selected');
        });
    });
    
    // If no radio is checked, check the first one (COD)
    const checkedRadio = Array.from(paymentRadios).find(radio => radio.checked);
    if (!checkedRadio && paymentRadios.length > 0) {
        paymentRadios[0].checked = true;
        paymentRadios[0].closest('.payment-option').classList.add('selected');
    }
}

// Toggle between saved addresses and new address form
function initAddressToggle() {
    const addNewBtn = document.getElementById('addNewAddressBtn');
    const cancelNewBtn = document.getElementById('cancelNewAddressBtn');
    const savedAddressesSection = document.getElementById('savedAddresses');
    const newAddressSection = document.getElementById('newAddressSection');
    const selectedAddressInput = document.getElementById('id_selected_address');
    const useNewAddressInput = document.getElementById('id_use_new_address');

    if (addNewBtn) {
        addNewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Hide saved addresses, show new address form
            if (savedAddressesSection) {
                savedAddressesSection.style.display = 'none';
            }
            if (newAddressSection) {
                newAddressSection.style.display = 'block';
            }

            // Update hidden inputs
            if (selectedAddressInput) {
                selectedAddressInput.value = '';
            }
            if (useNewAddressInput) {
                useNewAddressInput.value = 'true';
            }

            // Uncheck all address radios
            document.querySelectorAll('input[name="address_selection"]').forEach(radio => {
                radio.checked = false;
            });
            document.querySelectorAll('.address-card.selectable').forEach(card => {
                card.classList.remove('selected');
            });

            // Scroll to form
            newAddressSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    if (cancelNewBtn) {
        cancelNewBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show saved addresses, hide new address form
            if (savedAddressesSection) {
                savedAddressesSection.style.display = 'grid';
            }
            if (newAddressSection) {
                newAddressSection.style.display = 'none';
            }

            // Update hidden inputs - select default address
            const defaultRadio = document.querySelector('input[name="address_selection"]:checked') || 
                               document.querySelector('input[name="address_selection"]');
            
            if (defaultRadio) {
                defaultRadio.checked = true;
                defaultRadio.closest('.address-card').classList.add('selected');
                
                if (selectedAddressInput) {
                    selectedAddressInput.value = defaultRadio.value;
                }
            }

            if (useNewAddressInput) {
                useNewAddressInput.value = 'false';
            }

            // Clear new address form
            clearNewAddressForm();

            // Scroll to addresses
            if (savedAddressesSection) {
                savedAddressesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
}

function clearNewAddressForm() {
    const form = document.getElementById('checkoutForm');
    if (!form) return;

    const newAddressFields = ['full_name', 'phone', 'address_line', 'city', 'state', 'pincode', 'email'];
    newAddressFields.forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.value = '';
        }
    });

    // Clear error messages
    form.querySelectorAll('.form-error').forEach(error => {
        error.textContent = '';
    });
}

