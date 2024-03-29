# -*- coding: utf-8 -*-
import os

from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext as _

from apps.options.models import AudioOptions, VideoOptions
from apps.utils.common import nullable
from apps.video.stupff import FFmpegFile
from apps.video.tasks import ConvertVideoTask



class VideoFile(models.Model):
    class Meta:
        abstract = True

    def file_path(self):
        return self.file.path

    def ffmpeg_file(self, exists=True):
        return FFmpegFile(self.file_path(), exists)


class Original(VideoFile):
    title = models.CharField(_('Title'), max_length=40)
    file = models.FileField(upload_to='originals/', **nullable)
    enabled = models.BooleanField(verbose_name=_('Enabled'), default=True)

    def __unicode__(self):
        return u'{0}'.format(self.title)



class Converted(VideoFile):
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
    file = models.FileField(upload_to='converted/', **nullable)
    audio_options = models.ForeignKey(AudioOptions)
    video_options = models.ForeignKey(VideoOptions)
    splash_image = models.ImageField(_('Splash Image'),
                        upload_to='images/', max_length=200, **nullable)
    locked = models.BooleanField(('Locked'), default=True, editable=False)
    state = models.IntegerField(_('State'), default=PENDING, choices=STATE)

    def __unicode__(self):
        return u'{0}{1}{2}'.format(
            self.original.title, self.video_options, self.audio_options
        )

    def get_filename(self):
        return (str(self.original.id) +
            ''.join(self.audio_options.as_commandline()) +
            ''.join(self.video_options.as_commandline()) + '.mp4'
        )

    def rel_file_path(self):
        return self.file.field.generate_filename(
            self,
            self.get_filename()
        )

    def file_path(self):
        return self.file.storage.path(self.rel_file_path())


@receiver(post_save, sender=Converted)
def convert_from_original(sender, **kwargs):
    converted = kwargs['instance']
    if not converted.state is converted.PENDING:
        return
    ConvertVideoTask.delay(converted)

