from django.urls import path

from . import admin_views

app_name = "admin_panel"

urlpatterns = [
    # Authentication
    path("login/", admin_views.AdminLoginView.as_view(), name="login"),
    path("logout/", admin_views.AdminLogoutView.as_view(), name="logout"),
    
    # Dashboard
    path("", admin_views.AdminDashboardView.as_view(), name="dashboard"),
    
    # Categories
    path("categories/", admin_views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", admin_views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", admin_views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", admin_views.CategoryDeleteView.as_view(), name="category_delete"),
    
    # Products
    path("products/", admin_views.ProductListView.as_view(), name="product_list"),
    path("products/create/", admin_views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", admin_views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", admin_views.ProductDeleteView.as_view(), name="product_delete"),
    
    # Orders
    path("orders/", admin_views.OrderListView.as_view(), name="order_list"),
    path("orders/<slug:order_number>/", admin_views.OrderDetailView.as_view(), name="order_detail"),
    path("orders/<slug:order_number>/invoice/", admin_views.OrderInvoiceView.as_view(), name="order_invoice"),
    path("orders/<slug:order_number>/update-status/", admin_views.OrderUpdateStatusView.as_view(), name="order_update_status"),
    
    # Messages
    path("messages/", admin_views.MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/toggle-resolved/", admin_views.MessageToggleResolvedView.as_view(), name="message_toggle_resolved"),
]

