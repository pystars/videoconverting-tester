from celery.task import Task
from apps.video.models import Converted


class ConvertVideoTask(Task):
    """
    Converts the Video and creates the related files.
    """
    def run(self, converted, **kwargs):
        converted.state = Converted.PROCESSING
        converted.save()
        return "Ready"
