from django.core.management.base import BaseCommand, CommandError
from front.models import AccessToken
import os

class Command(BaseCommand):
    help = 'Clears and deletes expired exports'


    def handle(self, *args, **options):
        undeleted = AccessToken.objects.filter(deleted=False)

        for at in undeleted:
            if at.expired:
                try:
                    os.remove(at.file)
                except:
                    pass
                
                at.deleted = True
                at.save()
