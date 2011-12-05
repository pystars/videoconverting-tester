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
        for key in keys:
            yield self.OPTIONS.get(key)
            yield str(self.fields[key])

    def __unicode__(self):
        return ''.join(self.as_commandline(True))


class AudioOptions(Options):
    BITRATE_CHOICES = [(x, x) for x in (64, 96, 128, 160)]
    sample_rate = models.FloatField(
        'audio sampling frequency', **nullable)
    bitrate = models.PositiveIntegerField('audio bit rate',
        help_text='kbits/s (default like source)',
        choices=BITRATE_CHOICES, **nullable)

    class Meta:
        unique_together = (("sample_rate", "bitrate"),)

    OPTIONS = dict(
        sample_rate = '-R',
        bitrate = '-B',
    )


class VideoOptions(Options):

    PRESET_CHOICES = [ (x,x) for x in
        ('"Normal"', '"High Profile"', '"Classic"')
    ]

    RATE_CHOICES = [(x, x) for x in (5, 10, 12, 15, 23.976, 24, 25, 29.97)]
    codec = 'x264'
    preset = models.CharField('x264 preset', max_length=20,
                              choices=PRESET_CHOICES)
    bitrate = models.PositiveIntegerField('video bit rate',
        help_text='(bit/s)', **nullable)
    frame_rate = models.CharField('frame rate', max_length=10,
        help_text='(Hz value)', choices=RATE_CHOICES, **nullable)
    width = models.PositiveIntegerField('width')
    height = models.PositiveIntegerField('height', **nullable)
    quality = models.PositiveIntegerField('quality lvl',
        help_text='between 1 (excellent quality) and 31 (worst)', **nullable)
    x264opts = models.CharField('x264 options', max_length=400, **nullable)

    class Meta:
        unique_together = (
        ("frame_rate", "bitrate", "quality", "width", "height", "x264opts"),)

    OPTIONS = dict(
        preset = '-Z',
        bitrate = '-b',
        frame_rate = '-r',
        width = '-w',
        height = '-l',
        codec = '-e',
        quality = 'q'
    )

if __name__ == '__main__':
    import doctest
    doctest.testmod()
