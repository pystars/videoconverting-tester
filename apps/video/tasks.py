import subprocess
from celery.task import Task


class ConvertVideoTask(Task):
    extra_ffmpeg_args = []

    def get_commandline(self):
        return (
            ['ffmpeg', '-v', '10'] +
            self.extra_ffmpeg_args +
            ['-i', self.original_file.filename] +
            list(self.audio_options.as_commandline()) +
            list(self.video_options.as_commandline()) +
            [self.result_file.filename]
        )
    
    def run(self, converted, **kwargs):
        """
        Converts the Video and creates the related files.
        """
        logger = self.get_logger(**kwargs)
        logger.info("Starting Video Post conversion: %s" % converted)

        self.original_file = converted.original.ffmpeg_file()
        self.result_file = converted.ffmpeg_file(False)
        self.audio_options = converted.audio_options
        self.video_options = converted.video_options

        converted.state = converted.PROCESSING
        converted.save()
        process = subprocess.call(self.get_commandline(), shell=False)
        if process:
            converted.state = converted.ERROR
        else:
            converted.state = converted.READY
            converted.locked = False
        converted.save()
        return "Ready"
