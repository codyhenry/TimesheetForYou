from django.db import transaction

from .models import ParentSignature, TimeEntry


def replace_parent_signature_image(*, entry_id, image_name, image_content, approved_snapshot):
    """Replace an entry's parent signature image through a serialized path.

    The entry row is locked so concurrent re-sign requests for the same time
    entry serialize. The previous stored object is deleted only after the row
    points at the replacement image, keeping cleanup shared for API and admin
    replacement paths.
    """
    old_image_name = ""
    new_image_name = ""
    storage = None

    with transaction.atomic():
        entry = TimeEntry.objects.select_for_update().select_related("timesheet").get(pk=entry_id)
        signature = ParentSignature.objects.select_for_update().filter(entry=entry).first()
        if signature is None:
            signature = ParentSignature(entry=entry)
        else:
            old_image_name = signature.image.name or ""

        signature.image.save(image_name, image_content, save=False)
        signature.approved_snapshot = approved_snapshot
        signature.save()
        new_image_name = signature.image.name
        storage = signature.image.storage

        entry.signature_status = TimeEntry.SignatureStatus.SIGNED
        entry.save(update_fields=["signature_status", "updated_at"])
        signature.entry = entry

    if storage and old_image_name and old_image_name != new_image_name:
        storage.delete(old_image_name)

    return signature
