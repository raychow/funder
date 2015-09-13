import os

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it was a true
        # file system
        orig_name = name
        truncation = len(name) - max_length
        if truncation > 0:
            name = name[:-truncation]
        if not name:
            raise SuspiciousFileOperation(
                'Storage can not find an available filename for "%s". '
                'Please make sure that the corresponding file field '
                'allows sufficient "max_length".' % orig_name
            )
        if self.exists(name):
            os.remove(self.path(name))
        return name
