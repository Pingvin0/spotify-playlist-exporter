from django.db import models
from django.utils import timezone
from django.conf import settings
# Create your models here.
class AccessToken(models.Model):
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)

    key = models.CharField(max_length=255, unique=True)
    file = models.CharField(max_length=255, unique=True)

    deleted = models.BooleanField(default=False)

    ip_address = models.CharField(max_length=64)

    @property
    def expired(self):
        delta = (timezone.now() - self.created).total_seconds()
        return delta >= settings.SPOTIFY_EXPORT_EXPIRATION
    
    @property
    def download_name(self):
        return self.created.strftime('%Y-%m-%d_%H-%M_spotify-export.csv')
        
            