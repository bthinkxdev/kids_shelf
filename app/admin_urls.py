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
    
    # Products — list, create, edit, delete
    path("products/", admin_views.ProductListView.as_view(), name="product_list"),
    path("products/create/", admin_views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", admin_views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/update-basic/", admin_views.ProductUpdateBasicView.as_view(), name="product_update_basic"),
    path("products/<int:pk>/delete/", admin_views.ProductDeleteView.as_view(), name="product_delete"),

    # Product  — Step 1: create basic info
    path("products/create-basic/", admin_views.ProductCreateBasicView.as_view(), name="product_create_basic"),

    path("products/<int:pk>/images/", admin_views.ProductImagesListApiView.as_view(), name="product_images_list"),
    path("products/<int:pk>/images/upload/", admin_views.ProductImageUploadApiView.as_view(), name="product_image_upload"),
    path("products/images/<int:image_id>/delete/", admin_views.ProductImageDeleteApiView.as_view(), name="product_image_delete"),

    path("products/<int:pk>/formats/", admin_views.ProductFormatsListApiView.as_view(), name="product_formats_list"),
    path("products/<int:pk>/formats/add/", admin_views.ProductFormatAddApiView.as_view(), name="product_format_add"),
    
    # Orders
    path("orders/", admin_views.OrderListView.as_view(), name="order_list"),
    path("orders/<slug:order_number>/", admin_views.OrderDetailView.as_view(), name="order_detail"),
    path("orders/<slug:order_number>/invoice/", admin_views.OrderInvoiceView.as_view(), name="order_invoice"),
    path("orders/<slug:order_number>/update-status/", admin_views.OrderUpdateStatusView.as_view(), name="order_update_status"),
    
    # Messages
    path("messages/", admin_views.MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/toggle-resolved/", admin_views.MessageToggleResolvedView.as_view(), name="message_toggle_resolved"),

    # Age Groups
    path('age-groups/', admin_views.AgeGroupListView.as_view(), name='age_group_list'),
    path('age-groups/create/', admin_views.AgeGroupCreateView.as_view(), name='age_group_create'),
    path('age-groups/<int:pk>/edit/', admin_views.AgeGroupUpdateView.as_view(), name='age_group_update'),
    path('age-groups/<int:pk>/delete/', admin_views.AgeGroupDeleteView.as_view(), name='age_group_delete'),

    # Reviews
    path("reviews/", admin_views.ReviewListView.as_view(), name="review_list"),
]