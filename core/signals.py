import json
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
import datetime
from .models import Employee, VendorBankAccount, AdminBillInventory, ItemManagement, SystemLog

# Helper to serialize fields to JSON safely
def serialize_value(val):
    if isinstance(val, (Decimal, float)):
        return float(val)
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    return str(val)

# Watch models list
AUDITED_MODELS = [Employee, VendorBankAccount, AdminBillInventory, ItemManagement]

# Pre-save signal to store the old state of the instance
@receiver(pre_save)
def track_old_state(sender, instance, **kwargs):
    if sender not in AUDITED_MODELS:
        return
    
    if instance.pk:
        try:
            # Fetch the old instance from database
            old_instance = sender.objects.get(pk=instance.pk)
            # Store values in a private attribute
            instance._old_values = {}
            for field in sender._meta.fields:
                val = getattr(old_instance, field.name)
                # If foreign key, store the primary key
                if field.is_relation and val:
                    instance._old_values[field.name] = val.pk
                else:
                    instance._old_values[field.name] = val
        except sender.DoesNotExist:
            instance._old_values = None
    else:
        instance._old_values = None

# Post-save signal to log creation or updates
@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender not in AUDITED_MODELS:
        return
    
    # Exclude system fields from difference checking (like auto recalculations)
    # However, we still log them.
    
    model_name = sender.__name__
    record_id = str(instance.pk)
    record_name = str(instance)
    
    changes = {}
    
    if created:
        action = 'CREATE'
        # Log all fields
        for field in sender._meta.fields:
            val = getattr(instance, field.name)
            if field.is_relation and val:
                changes[field.name] = {
                    "new": serialize_value(val.pk)
                }
            else:
                changes[field.name] = {
                    "new": serialize_value(val)
                }
    else:
        action = 'UPDATE'
        old_values = getattr(instance, '_old_values', None)
        if old_values:
            for field in sender._meta.fields:
                val = getattr(instance, field.name)
                curr_val = val.pk if field.is_relation and val else val
                old_val = old_values.get(field.name)
                
                # Compare serialized string representations to be safe with floats/decimals
                if serialize_value(curr_val) != serialize_value(old_val):
                    changes[field.name] = {
                        "old": serialize_value(old_val),
                        "new": serialize_value(curr_val)
                    }
        else:
            # Fallback if old values weren't captured
            changes = {"message": "Updated details (previous state not captured)"}
            
    # Don't log if there are no changes on updates
    if action == 'UPDATE' and not changes:
        return

    SystemLog.objects.create(
        action=action,
        model_name=model_name,
        record_id=record_id,
        record_name=record_name,
        changed_fields=json.dumps(changes, indent=2)
    )

# Post-delete signal to log deletions
@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender not in AUDITED_MODELS:
        return
    
    model_name = sender.__name__
    record_id = str(instance.pk)
    record_name = str(instance)
    
    changes = {}
    for field in sender._meta.fields:
        val = getattr(instance, field.name)
        if field.is_relation and val:
            changes[field.name] = {"old": serialize_value(val.pk)}
        else:
            changes[field.name] = {"old": serialize_value(val)}

    SystemLog.objects.create(
        action='DELETE',
        model_name=model_name,
        record_id=record_id,
        record_name=record_name,
        changed_fields=json.dumps(changes, indent=2)
    )
