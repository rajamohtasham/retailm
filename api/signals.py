import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from .models import StockMovement, AuditLog


# --- Update product quantity on stock movements ---
@receiver(post_save, sender=StockMovement)
def update_product_quantity(sender, instance, created, **kwargs):
    if not created:
        return
    product = instance.product
    if instance.movement_type in ["in", "return"]:
        product.quantity += abs(instance.quantity)
    elif instance.movement_type in ["out", "damage"]:
        product.quantity -= abs(instance.quantity)
    elif instance.movement_type == "adjustment":
        product.quantity += instance.quantity  # signed delta
    product.save()


# --- Log CREATE / UPDATE actions ---
@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    # Prevent recursion
    if sender is AuditLog:
        return

    # Only log models in our app
    if not hasattr(instance, '_meta') or instance._meta.app_label != 'api':
        return

    action = 'create' if created else 'update'
    user = getattr(instance, 'created_by', None) or getattr(instance, 'user', None)

    changes = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if hasattr(value, 'pk'):
            changes[field.name] = value.pk
        else:
            changes[field.name] = str(value)

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        changes=json.dumps(changes, cls=DjangoJSONEncoder),
    )


# --- Log DELETE actions ---
@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    # Prevent recursion
    if sender is AuditLog:
        return

    # Only log models in our app
    if not hasattr(instance, '_meta') or instance._meta.app_label != 'api':
        return

    user = getattr(instance, 'created_by', None) or getattr(instance, 'user', None)

    # Capture the final state before deletion
    changes = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name, None)
        if hasattr(value, 'pk'):
            changes[field.name] = value.pk
        else:
            changes[field.name] = str(value)

    AuditLog.objects.create(
        user=user,
        action='delete',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        changes=json.dumps(changes, cls=DjangoJSONEncoder),
    )
