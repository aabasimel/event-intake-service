from django.db import models

class Event(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    received_at = models.DateTimeField()
    client_ts = models.DateTimeField()
    event = models.CharField(max_length=64)
    user_id = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict)
    request_id = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.id}: {self.event}"

