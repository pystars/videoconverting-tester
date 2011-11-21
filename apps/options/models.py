from django.db import models


nullable = dict(null=True, blank=True)


class Options(models.Model):
    """
    Dict-like interface abstracting FFmpeg command line flags.

    Example::

        >>> opt = AudioOptions(codec='vp8', bitrate=150000)
        >>> opt.bitrate
        150000
        >>> list(opt.as_commandline())
        ['-acodec', 'vp8', '-ab', '150000']
    """
    empty = ()
    OPTIONS = {}

    class Meta:
        abstract = True

    @property
    def fields(self):
        return dict((k,v) for k, v in self.__dict__.iteritems()
            if v and k in self.OPTIONS.keys())

    def as_commandline(self, include_special=False):
        keys = self.fields.keys()
        if not include_special:
            keys = [k for k in keys if self.OPTIONS.get(k)]
        if not keys:
            for item in self.empty:
                yield item
        for key in keys:
            yield '-' + self.OPTIONS.get(key)
            yield str(self.fields[key])

    def __unicode__(self):
        return ''.join(self.as_commandline(True))


class AudioOptions(Options):
    sample_rate = models.PositiveIntegerField(
        'audio sampling frequency', **nullable)
    bitrate = models.PositiveIntegerField('audio bit rate',
        help_text='bit/s (default = 64k)', **nullable)
    quality = models.CharField('audio quality', max_length=10,
        help_text='(codec-specific, VBR)', **nullable)
    channels = models.PositiveIntegerField(
        'number of audio channels', **nullable)
    codec = models.CharField('audio codec', max_length=10,
        help_text="""Use the "copy" special value to specify that the raw
        codec data must be copied as is""", **nullable)

    class Meta:
        unique_together = (
            ("sample_rate", "bitrate", "quality", "channels", "codec"),
        )

    empty = ['-an'] # -an = no audio
    OPTIONS = dict(
        sample_rate = 'ar',
        bitrate = 'ab',
        quality = 'aq',
        channels = 'ac',
        codec = 'acodec'
    )


class VideoOptions(Options):
    bitrate = models.PositiveIntegerField('video bit rate',
        help_text='(bit/s)', **nullable)
    frame_rate = models.CharField('frame rate', max_length=10,
        help_text='(Hz value)', **nullable)
    frames = models.PositiveIntegerField('frames',
        help_text='number of video frames to record', **nullable)
    size = models.CharField('frame size', max_length=10,
        help_text='The format is wxh (160x128)', **nullable)
    codec = models.CharField("video codec", max_length=20,
       help_text="""Use the "copy" special value to tell that the raw codec
       data must be copied as is""", **nullable)
    quality = models.PositiveIntegerField('quality lvl',
        help_text='between 1 (excellent quality) and 31 (worst)', **nullable)
    max_width = models.PositiveIntegerField(**nullable)
    max_height = models.PositiveIntegerField(**nullable)

    class Meta:
        unique_together = (
            ("frame_rate", "bitrate", "quality", "frames", "codec", "size",
             "max_width", "max_height"),
        )

    OPTIONS = dict(
        bitrate = 'b',
        frame_rate = 'r',
        frames = 'vframes',
        size = 's',
        codec = 'vcodec',
        quality = 'qscale',
        max_width = None,
        max_height = None
    )
    empty = ()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
