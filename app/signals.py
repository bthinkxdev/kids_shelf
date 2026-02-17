from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import ProductImage, Category


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """
    Delete image file when ProductImage instance is deleted
    Works for both local storage and S3
    """
    if instance.image:
        try:
            instance.image.storage.delete(instance.image.name)
        except Exception:
            # Silently fail if file doesn't exist or storage error
            pass


@receiver(pre_save, sender=ProductImage)
def delete_old_product_image_on_update(sender, instance, **kwargs):
    """
    Delete old image file when ProductImage is updated with a new image
    Works for both local storage and S3
    """
    if not instance.pk:
        return False

    try:
        old_image = ProductImage.objects.get(pk=instance.pk).image
    except ProductImage.DoesNotExist:
        return False

    # If image has changed, delete the old one
    if old_image and old_image != instance.image:
        try:
            old_image.storage.delete(old_image.name)
        except Exception:
            # Silently fail if file doesn't exist or storage error
            pass


@receiver(post_delete, sender=Category)
def delete_category_image_file(sender, instance, **kwargs):
    """
    Delete image file when Category instance is deleted
    Works for both local storage and S3
    """
    if instance.image:
        try:
            instance.image.storage.delete(instance.image.name)
        except Exception:
            # Silently fail if file doesn't exist or storage error
            pass


@receiver(pre_save, sender=Category)
def delete_old_category_image_on_update(sender, instance, **kwargs):
    """
    Delete old image file when Category is updated with a new image
    Works for both local storage and S3
    """
    if not instance.pk:
        return False

    try:
        old_image = Category.objects.get(pk=instance.pk).image
    except Category.DoesNotExist:
        return False

    # If image has changed, delete the old one
    if old_image and old_image != instance.image:
        try:
            old_image.storage.delete(old_image.name)
        except Exception:
            # Silently fail if file doesn't exist or storage error
            pass