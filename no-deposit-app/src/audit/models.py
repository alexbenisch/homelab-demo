from django.db import models


class AuditLog(models.Model):
    """Immutable append-only audit trail. Every status change is recorded here."""

    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    actor_id = models.CharField(max_length=255)
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("AuditLog entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog entries cannot be deleted.")

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.entity_type}#{self.entity_id} {self.action}"

    @classmethod
    def record(
        cls, *, entity_type: str, entity_id, action: str, actor_id: str, actor_ip=None, payload=None
    ):
        return cls.objects.create(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            actor_id=actor_id,
            actor_ip=actor_ip,
            payload=payload or {},
        )
