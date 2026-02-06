import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import ProductImage, Category


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """
    Delete image file from disk when ProductImage instance is deleted
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(pre_save, sender=ProductImage)
def delete_old_product_image_on_update(sender, instance, **kwargs):
    """
    Delete old image file when ProductImage is updated with a new image
    """
    if not instance.pk:
        return False

    try:
        old_image = ProductImage.objects.get(pk=instance.pk).image
    except ProductImage.DoesNotExist:
        return False

    # If image has changed, delete the old one
    if old_image and old_image != instance.image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)


@receiver(post_delete, sender=Category)
def delete_category_image_file(sender, instance, **kwargs):
    """
    Delete image file from disk when Category instance is deleted
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(pre_save, sender=Category)
def delete_old_category_image_on_update(sender, instance, **kwargs):
    """
    Delete old image file when Category is updated with a new image
    """
    if not instance.pk:
        return False

    try:
        old_image = Category.objects.get(pk=instance.pk).image
    except Category.DoesNotExist:
        return False

    # If image has changed, delete the old one
    if old_image and old_image != instance.image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)


