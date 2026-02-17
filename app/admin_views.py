from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum, Q, F, Prefetch
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from datetime import timedelta

from .models import (
    Category,
    ContactMessage,
    Order,
    OrderItem,
    Product,
    ProductImage,
    BookFormat,
    AgeGroup,
    Review
)
from .admin_forms import (
    AdminLoginForm,
    CategoryForm,
    ProductForm,
    ProductBasicForm,
    ProductImageFormSet,
    BookFormatFormSet, 
    _validate_image_file,
)
from django import forms
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.utils.dateparse import parse_date

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff/admin access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect("admin_panel:login")
        messages.error(self.request, "You don't have permission to access this area.")
        return redirect("store:home")


# Authentication Views
class AdminLoginView(View):
    template_name = "admin/login.html"
    
    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("admin_panel:dashboard")
        form = AdminLoginForm()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request):
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("admin_panel:dashboard")
            else:
                messages.error(request, "Invalid credentials or insufficient permissions.")
        
        return render(request, self.template_name, {"form": form})


class AdminLogoutView(View):
    def post(self, request):
        logout(request)
        messages.success(request, "Logged out successfully.")
        return redirect("admin_panel:login")


# Dashboard View
class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "admin/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date filters
        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # Order statistics
        total_orders = Order.objects.count()
        orders_today = Order.objects.filter(created_at__date=today).count()
        orders_this_week = Order.objects.filter(created_at__date__gte=last_7_days).count()
        orders_this_month = Order.objects.filter(created_at__date__gte=last_30_days).count()
        
        # Revenue statistics
        total_revenue = Order.objects.aggregate(total=Sum("total"))["total"] or 0
        revenue_today = Order.objects.filter(created_at__date=today).aggregate(total=Sum("total"))["total"] or 0
        revenue_this_week = Order.objects.filter(created_at__date__gte=last_7_days).aggregate(total=Sum("total"))["total"] or 0
        revenue_this_month = Order.objects.filter(created_at__date__gte=last_30_days).aggregate(total=Sum("total"))["total"] or 0
        
        # Order status breakdown
        order_status = Order.objects.values("status").annotate(count=Count("id"))
        
        # Product statistics
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_products = BookFormat.objects.filter(
            is_active=True,
            stock_quantity__lte=5,
            stock_quantity__gt=0
        ).count()
        out_of_stock_products = BookFormat.objects.filter(
            is_active=True,
            stock_quantity=0
        ).count()
        
        # Recent orders
        recent_orders = Order.objects.select_related("address").order_by("-created_at")[:10]
        
        # Top selling products (last 30 days)
        top_products = (
            Product.objects.filter(
                order_items__order__created_at__gte=last_30_days
            )
            .annotate(
                total_sold=Sum("order_items__quantity"),
                revenue=Sum(F("order_items__quantity") * F("order_items__unit_price"))
            )
            .order_by("-total_sold")[:5]
        )
        
        # Recent messages
        unresolved_messages = ContactMessage.objects.filter(is_resolved=False).count()
        
        # Daily revenue chart data (last 14 days)
        import json
        chart_data = []
        for i in range(13, -1, -1):
            date = today - timedelta(days=i)
            daily_revenue = Order.objects.filter(
                created_at__date=date
            ).aggregate(total=Sum("total"))["total"] or 0
            chart_data.append({
                "date": date.strftime("%d %b"),
                "revenue": float(daily_revenue)
            })
        chart_data_json = json.dumps(chart_data)
        
        context.update({
            "total_orders": total_orders,
            "orders_today": orders_today,
            "orders_this_week": orders_this_week,
            "orders_this_month": orders_this_month,
            "total_revenue": total_revenue,
            "revenue_today": revenue_today,
            "revenue_this_week": revenue_this_week,
            "revenue_this_month": revenue_this_month,
            "order_status": order_status,
            "total_products": total_products,
            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "recent_orders": recent_orders,
            "top_products": top_products,
            "unresolved_messages": unresolved_messages,
            "chart_data": chart_data_json,
            "active_menu": "dashboard",
        })
        
        return context


# Category Management Views
class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = "admin/category_list.html"
    context_object_name = "categories"
    paginate_by = 20
    
    def get_queryset(self):
        qs = Category.objects.annotate(product_count=Count("products"))
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search))
        return qs.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "categories"
        context["search_query"] = self.request.GET.get("search", "")
        return context


class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "admin/category_form.html"
    success_url = reverse_lazy("admin_panel:category_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Category created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "categories"
        context["form_title"] = "Create Category"
        return context


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "admin/category_form.html"
    success_url = reverse_lazy("admin_panel:category_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "categories"
        context["form_title"] = "Edit Category"
        return context


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("admin_panel:category_list")
    
    def post(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            messages.error(request, "Cannot delete category with existing products.")
            return redirect("admin_panel:category_list")
        
        messages.success(request, f"Category '{category.name}' deleted successfully!")
        return super().post(request, *args, **kwargs)


# Product Management Views
class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = "admin/product_list.html"
    context_object_name = "products"
    paginate_by = 20
    
    def get_queryset(self):
        qs = Product.objects.select_related("category").prefetch_related(
            "images", 
            "formats",
            Prefetch("age_groups", queryset=AgeGroup.objects.filter(is_active=True).order_by('display_order'))  # ADD THIS
        )
        search = self.request.GET.get("search")
        category = self.request.GET.get("category")
        status = self.request.GET.get("status")
        age_group = self.request.GET.get("age_group")
        
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if category:
            qs = qs.filter(category_id=category)
        if age_group:
            qs = qs.filter(age_groups__slug=age_group, age_groups__is_active=True)
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)
        
        return qs.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "products"
        context["categories"] = Category.objects.filter(is_active=True)
        context["age_groups"] = AgeGroup.objects.filter(is_active=True).order_by('display_order')
        context["search_query"] = self.request.GET.get("search", "")
        context["filter_category"] = self.request.GET.get("category", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["filter_age_group"] = self.request.GET.get("age_group", "")
        
        # ✅ ROBUSTNESS: Add stock info to each product
        for product in context["products"]:
            try:
                product.total_stock = product.get_total_stock()
                product.has_stock = product.has_available_stock()
                product.available_formats_count = product.get_available_formats().count()
            except Exception:
                product.total_stock = 0
                product.has_stock = False
                product.available_formats_count = 0
        
        return context


class ProductCreateView(StaffRequiredMixin, TemplateView):
    
    template_name = "admin/product_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["basic_form"] = ProductBasicForm(instance=None)
        context["age_groups"] = AgeGroup.objects.filter(is_active=True).order_by("display_order")
        context["active_menu"] = "products"
        context["form_title"] = "Add Book"
        return context
    
class ProductUpdateView(StaffRequiredMixin, View):
    
    template_name = "admin/product_edit_form.html"

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        basic_form = ProductBasicForm(instance=product)
        age_groups = AgeGroup.objects.filter(is_active=True).order_by("display_order")
        # Pre-selected age groups for this product
        product_age_groups = product.age_groups.filter(is_active=True)
        return render(request, self.template_name, {
            "product": product,
            "basic_form": basic_form,
            "age_groups": age_groups,
            "product_age_groups": product_age_groups,
            "active_menu": "products",
            "form_title": f"Edit Book — {product.name}",
        })
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]
        format_formset = context["format_formset"]
        
        if not image_formset.is_valid():
            for error in image_formset.non_form_errors():
                messages.error(self.request, f"Image error: {error}")
            for form_item in image_formset.forms:
                for field, errors in form_item.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Image {field}: {error}")
            return self.form_invalid(form)
        
        if not format_formset.is_valid():
            for error in format_formset.non_form_errors():
                messages.error(self.request, f"Format error: {error}")
            for form_item in format_formset.forms:
                for field, errors in form_item.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Format {field}: {error}")
            return self.form_invalid(form)
        
        from django.db import transaction
        try:
            with transaction.atomic():
                self.object = form.save()
                image_formset.instance = self.object
                image_formset.save()
                format_formset.instance = self.object
                format_formset.save()
                
                messages.success(
                    self.request, 
                    f"✅ Book '{self.object.name}' updated successfully!"
                )
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(self.request, f"❌ Error updating book: {str(e)}")
            return self.form_invalid(form)

class ProductUpdateBasicView(StaffRequiredMixin, View):

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': ['Invalid JSON data']}
            }, status=400)

        # Extract age_groups before passing to form
        age_group_ids = data.pop('age_groups', []) or []

        form = ProductBasicForm(data, instance=product)

        if form.is_valid():
            from django.db import transaction
            try:
                with transaction.atomic():
                    product = form.save()

                    # Handle age_groups M2M
                    if age_group_ids:
                        valid_age_groups = AgeGroup.objects.filter(
                            id__in=age_group_ids,
                            is_active=True
                        )
                        product.age_groups.set(valid_age_groups)
                    else:
                        product.age_groups.clear()

                    return JsonResponse({
                        'success': True,
                        'product': {
                            'name': product.name,
                            'price': str(product.price),
                            'author': product.author,
                        }
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                }, status=500)

        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(e) for e in error_list]

        return JsonResponse({'success': False, 'errors': errors}, status=400)
class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("admin_panel:product_list")
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        
        # Check if product has orders
        try:
            if product.order_items.exists():
                messages.error(
                    request, 
                    f"Cannot delete '{product_name}' because it has been ordered. "
                    "Deactivate it instead by editing and unchecking 'Active'."
                )
                return redirect("admin_panel:product_list")
        except Exception:
            pass  # Continue with other checks
        
        # Check if product formats are in any carts
        try:
            cart_count = product.cart_items.count()
            if cart_count > 0:
                messages.error(
                    request,
                    f"Cannot delete '{product_name}' because it's in {cart_count} cart(s). "
                    "Deactivate the product or wait for carts to clear."
                )
                return redirect("admin_panel:product_list")
        except Exception:
            pass  # Continue with deletion
        
        from django.db import transaction
        try:
            with transaction.atomic():
                # Delete formats first
                product.formats.all().delete()
                
                # Delete images
                product.images.all().delete()
                
                # Delete product
                product.delete()
                
                messages.success(request, f"Product '{product_name}' deleted successfully!")
                return redirect("admin_panel:product_list")
                
        except Exception as e:
            messages.error(request, f"Error deleting product: {str(e)}")
            return redirect("admin_panel:product_list")


# Order Management Views
class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = "admin/order_list.html"
    context_object_name = "orders"
    paginate_by = 20
    
    def get_queryset(self):
        qs = Order.objects.select_related("address").prefetch_related("items")
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(address__full_name__icontains=search) |
                Q(address__phone__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        
        return qs.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "orders"
        context["search_query"] = self.request.GET.get("search", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["status_choices"] = Order.Status.choices
        return context


class OrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = "admin/order_detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"
    
    def get_queryset(self):
        return Order.objects.select_related("address", "payment").prefetch_related(
            "items__product", "items__variant"
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "orders"
        context["status_choices"] = Order.Status.choices
        return context


class OrderInvoiceView(StaffRequiredMixin, DetailView):
    """Professional A4 Invoice view for printing"""
    model = Order
    template_name = "admin/order_invoice.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"
    
    def get_queryset(self):
        return Order.objects.select_related("address", "payment").prefetch_related(
            "items__product", "items__variant"
        )


class OrderUpdateStatusView(StaffRequiredMixin, View):
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        new_status = request.POST.get("status")
        
        if new_status in dict(Order.Status.choices):
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(request, f"Order status updated to {order.get_status_display()}.")
        else:
            messages.error(request, "Invalid status.")
        
        return redirect("admin_panel:order_detail", order_number=order_number)


# Contact Messages Management
class MessageListView(StaffRequiredMixin, ListView):
    model = ContactMessage
    template_name = "admin/message_list.html"
    context_object_name = "messages"
    paginate_by = 20
    
    def get_queryset(self):
        qs = ContactMessage.objects.all()
        status = self.request.GET.get("status")
        
        if status == "unresolved":
            qs = qs.filter(is_resolved=False)
        elif status == "resolved":
            qs = qs.filter(is_resolved=True)
        
        return qs.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "messages"
        context["filter_status"] = self.request.GET.get("status", "")
        return context


class MessageToggleResolvedView(StaffRequiredMixin, View):
    def post(self, request, pk):
        message = get_object_or_404(ContactMessage, pk=pk)
        message.is_resolved = not message.is_resolved
        message.save(update_fields=["is_resolved"])
        
        status_text = "resolved" if message.is_resolved else "unresolved"
        messages.success(request, f"Message marked as {status_text}.")
        
        return redirect("admin_panel:message_list")

# Age Group Management Views
class AgeGroupListView(StaffRequiredMixin, ListView):
    model = AgeGroup
    template_name = "admin/age_group_list.html"
    context_object_name = "age_groups"
    
    def get_queryset(self):
        return AgeGroup.objects.all().order_by('display_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "age_groups"
        return context


class AgeGroupCreateView(StaffRequiredMixin, CreateView):
    model = AgeGroup
    fields = ['name', 'emoji', 'display_order', 'is_active']
    template_name = "admin/age_group_form.html"
    success_url = reverse_lazy("admin_panel:age_group_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Age group created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "age_groups"
        context["form_title"] = "Create Age Group"
        return context


class AgeGroupUpdateView(StaffRequiredMixin, UpdateView):
    model = AgeGroup
    fields = ['name', 'emoji', 'display_order', 'is_active']
    template_name = "admin/age_group_form.html"
    success_url = reverse_lazy("admin_panel:age_group_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Age group updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_menu"] = "age_groups"
        context["form_title"] = "Edit Age Group"
        return context


class AgeGroupDeleteView(StaffRequiredMixin, DeleteView):
    model = AgeGroup
    success_url = reverse_lazy("admin_panel:age_group_list")
    
    def post(self, request, *args, **kwargs):
        age_group = self.get_object()
        messages.success(request, f"Age group '{age_group.name}' deleted successfully!")
        return super().post(request, *args, **kwargs)
    
# AJAX API VIEWS FOR PRODUCT CREATION
class ProductCreateBasicView(StaffRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': ['Invalid JSON data']}
            }, status=400)

        # Extract age_groups before passing to form (M2M can't go through ModelForm via JSON)
        age_group_ids = data.pop('age_groups', []) or []

        form = ProductBasicForm(data)

        if form.is_valid():
            from django.db import transaction
            try:
                with transaction.atomic():
                    product = form.save()

                    # Handle age_groups M2M separately
                    if age_group_ids:
                        valid_age_groups = AgeGroup.objects.filter(
                            id__in=age_group_ids,
                            is_active=True
                        )
                        product.age_groups.set(valid_age_groups)
                    else:
                        product.age_groups.clear()

                    return JsonResponse({
                        'success': True,
                        'product_id': product.id,
                        'product': {
                            'name': product.name,
                            'price': str(product.price),
                            'author': product.author,
                            'category_name': product.category.name if product.category else ''
                        }
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [str(e)]}
                }, status=500)

        # Return form errors
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(e) for e in error_list]

        return JsonResponse({'success': False, 'errors': errors}, status=400)


class ProductFormatsListApiView(StaffRequiredMixin, View):
    """✅ ROBUSTNESS: Get all formats for a product"""
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            formats = []
            
            for fmt in product.formats.all().order_by('format_type'):
                formats.append({
                    'id': fmt.id,
                    'sku': fmt.sku,
                    'format_type': fmt.format_type,
                    'format_type_display': fmt.get_format_type_display(),
                    'stock_quantity': fmt.stock_quantity,
                    'is_active': fmt.is_active,
                    'is_available': fmt.is_available()
                })
            
            return JsonResponse({'formats': formats})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ProductFormatAddApiView(StaffRequiredMixin, View):
    """✅ ROBUSTNESS: Add a single format to existing product"""
    def post(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': ['Invalid JSON data']}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=404)
        
        # Validate
        errors = {}
        sku = (data.get('sku') or '').strip()
        format_type = data.get('format_type')
        stock_quantity = data.get('stock_quantity', 0)
        
        if not sku:
            errors['sku'] = ['SKU is required']
        elif BookFormat.objects.filter(sku=sku).exists():
            errors['sku'] = ['SKU already exists']
        
        if not format_type:
            errors['format_type'] = ['Format type is required']
        elif BookFormat.objects.filter(product=product, format_type=format_type).exists():
            errors['format_type'] = ['This format already exists for this product']
        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                errors['stock_quantity'] = ['Stock cannot be negative']
        except (TypeError, ValueError):
            errors['stock_quantity'] = ['Invalid stock quantity']
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # Create format
        from django.db import transaction
        try:
            with transaction.atomic():
                book_format = BookFormat.objects.create(
                    product=product,
                    sku=sku,
                    format_type=format_type,
                    stock_quantity=stock_quantity,
                    is_active=data.get('is_active', True)
                )
                
                return JsonResponse({
                    'success': True,
                    'format_id': book_format.id,
                    'format': {
                        'id': book_format.id,
                        'sku': book_format.sku,
                        'format_type': book_format.format_type,
                        'format_type_display': book_format.get_format_type_display(),
                        'stock_quantity': book_format.stock_quantity,
                        'is_active': book_format.is_active
                    }
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=500)


class ProductImageUploadApiView(StaffRequiredMixin, View):
    """✅ ROBUSTNESS: Upload a single image to existing product"""
    def post(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=404)
        
        # Check image count
        if product.images.count() >= 5:
            return JsonResponse({
                'success': False,
                'errors': {'image': ['Maximum 5 images allowed']}
            }, status=400)
        
        image = request.FILES.get('image')
        if not image:
            return JsonResponse({
                'success': False,
                'errors': {'image': ['No image provided']}
            }, status=400)
        
        # Validate image
        try:
            _validate_image_file(image, required=True)
        except forms.ValidationError as e:
            return JsonResponse({
                'success': False,
                'errors': {'image': e.messages}
            }, status=400)
        
        # Create image
        from django.db import transaction
        try:
            with transaction.atomic():
                # If this is first image, make it primary
                is_first = product.images.count() == 0
                
                product_image = ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=is_first,
                    alt_text=request.POST.get('alt_text', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'image_id': product_image.id,
                    'image': {
                        'id': product_image.id,
                        'url': product_image.image.url if product_image.image else None,
                        'is_primary': product_image.is_primary,
                        'alt_text': product_image.alt_text
                    }
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'image': [str(e)]}
            }, status=500)


class ProductImagesListApiView(StaffRequiredMixin, View):
    """✅ ROBUSTNESS: Get all images for a product"""
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            images = []
            
            for img in product.images.all().order_by('-is_primary', 'id'):
                images.append({
                    'id': img.id,
                    'url': img.image.url if img.image else None,
                    'is_primary': img.is_primary,
                    'alt_text': img.alt_text
                })
            
            return JsonResponse({'images': images})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ProductImageDeleteApiView(StaffRequiredMixin, View):
    """✅ ROBUSTNESS: Delete a product image"""
    def post(self, request, image_id):
        try:
            image = get_object_or_404(ProductImage, id=image_id)
            image.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Image deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
        
class ReviewListView(StaffRequiredMixin, TemplateView):
    """
    Admin moderation panel for Ratings & Reviews.
    Filters: product, rating, date range, approval status.
    Bulk actions: approve, unapprove, soft-delete.
    """

    template_name = "admin/review_list.html"
    paginate_by = 25

    def get_queryset(self):
        qs = Review.objects.select_related("product", "user", "order").filter(
            is_deleted=False
        )

        request = self.request
        q = (request.GET.get("q") or "").strip()
        product_id = request.GET.get("product")
        rating = request.GET.get("rating")
        status = request.GET.get("status")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if q:
            qs = qs.filter(
                Q(product__name__icontains=q)
                | Q(user__username__icontains=q)
                | Q(user__email__icontains=q)
            )
        if product_id:
            try:
                qs = qs.filter(product_id=int(product_id))
            except (TypeError, ValueError):
                pass
        if rating:
            try:
                qs = qs.filter(rating=int(rating))
            except (TypeError, ValueError):
                pass
        if status == "approved":
            qs = qs.filter(is_approved=True)
        elif status == "unapproved":
            qs = qs.filter(is_approved=False)
        if date_from:
            try:
                df = parse_date(date_from)
                if df:
                    qs = qs.filter(created_at__date__gte=df)
            except Exception:
                pass
        if date_to:
            try:
                dt = parse_date(date_to)
                if dt:
                    qs = qs.filter(created_at__date__lte=dt)
            except Exception:
                pass

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        paginator = Paginator(qs, self.paginate_by)
        page_number = self.request.GET.get("page")
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context["active_menu"] = "reviews"
        context["reviews"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["is_paginated"] = paginator.num_pages > 1
        context["products"] = Product.objects.order_by("name").only("id", "name")
        context["filter_q"] = (self.request.GET.get("q") or "").strip()
        context["filter_product"] = self.request.GET.get("product") or ""
        context["filter_rating"] = self.request.GET.get("rating") or ""
        context["filter_status"] = self.request.GET.get("status") or ""
        context["filter_date_from"] = self.request.GET.get("date_from") or ""
        context["filter_date_to"] = self.request.GET.get("date_to") or ""
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("selected")
        if not action or not ids:
            messages.warning(request, "Please select at least one review and an action.")
            return redirect("admin_panel:review_list")

        try:
            ids_int = [int(x) for x in ids]
        except (TypeError, ValueError):
            messages.error(request, "Invalid review selection.")
            return redirect("admin_panel:review_list")

        reviews = list(
            Review.objects.select_for_update()
            .select_related("product")
            .filter(id__in=ids_int)
        )
        if not reviews:
            messages.info(request, "No reviews found for the selected IDs.")
            return redirect("admin_panel:review_list")

        if action == "approve":
            for r in reviews:
                if not r.is_approved and not r.is_deleted:
                    r.is_approved = True
                    r.save(update_fields=["is_approved"])
            messages.success(request, "Selected reviews have been approved.")
        elif action == "unapprove":
            for r in reviews:
                if r.is_approved and not r.is_deleted:
                    r.is_approved = False
                    r.save(update_fields=["is_approved"])
            messages.success(request, "Selected reviews have been unapproved.")
        elif action == "delete":
            for r in reviews:
                if not r.is_deleted:
                    r.is_deleted = True
                    r.save(update_fields=["is_deleted"])
            messages.success(request, "Selected reviews have been deleted.")
        else:
            messages.error(request, "Unknown action.")

        return redirect("admin_panel:review_list")