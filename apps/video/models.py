# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext as _
import os

from apps.options.models import AudioOptions, VideoOptions
#from django.conf import settings
#from django.template.defaultfilters import slugify
from apps.utils.common import nullable
from apps.video.stupff import convert_file


class Original(models.Model):
    title = models.CharField(_('Title'), max_length=40)
    file = models.FileField('Файл для загрузки', upload_to='originals/')
    enabled = models.BooleanField(verbose_name=_('Enabled'), default=True)

    def __unicode__(self):
        return u'{0}'.format(self.title)


class Converted(models.Model):
    PENDING = 0
    PROCESSING = 1
    READY = 2
    ERROR = 3
    STATE = (
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing')),
        (READY, _('Ready')),
        (ERROR, _('Error')),
    )
    original = models.ForeignKey(Original)
    audio_options = models.ForeignKey(AudioOptions)
    video_options = models.ForeignKey(VideoOptions)
    file = models.FileField(upload_to='converted/', **nullable)
    splash_image = models.ImageField(_('Splash Image'),
                        upload_to='images/', max_length=200, **nullable)
    locked = models.BooleanField(('Locked'), default=True)
    state = models.IntegerField(_('State'), default=PENDING, choices=STATE)

    def __unicode__(self):
        return u'{0}{1}{2}'.format(
            self.original.title, self.video_options, self.audio_options
        )

    def generate_file_path(self):
        return self.file.storage.path(self.file.field.generate_filename(
            self,
            str(self.original.id) +
            ''.join(self.audio_options.as_commandline()) +
            ''.join(self.video_options.as_commandline()) + '.mp4'
        ))


@receiver(post_save, sender=Converted)
def convert_from_original(sender, **kwargs):
    converted = kwargs['instance']
    file_path = converted.generate_file_path()
    print file_path
    if os.path.exists(file_path):
        return
    convert_file(
        converted.original.file.path,
        file_path,
        audio_options = converted.audio_options,
        video_options = converted.video_options
    )
    converted.state = sender.READY
    converted.locked = False
    converted.save()
    print 'converted'
