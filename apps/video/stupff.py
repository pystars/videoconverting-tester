from __future__ import division
import time
from subprocess import Popen, PIPE

from mediainfo import get_metadata as get_file_metadata

from utils import *


class FFmpegError(Exception):
    pass

class InvalidInputError(FFmpegError):
    pass


class FFmpegSubprocess(Popen):
    def __init__(self, *args, **kwargs):
        self._procname = args[0][0]
        Popen.__init__(self, *args, **kwargs)

    def wait(self):
        raise SystemError("Use safe_wait(). wait() sucks. (see bug #1731717)")

    def safe_wait(self):
        # mimics the bahaviour of `.wait()`, but hopefully with a lot smaller
        # chance to hit Python bug #1731717 (which crashes calls to `waitpid`,
        # and thus to `.wait()`, `.poll()`, ... randomly)
        while not self.finished():
            time.sleep(0.1)

    def successful(self):
        assert self.finished()
        return self.returncode == 0

    def finished(self):
        return self.poll() is not None

    def raise_error(self):
        assert not self.successful()
        if self.returncode in [234]:
            raise InvalidInputError(self._procname, self.returncode)
        else:
            raise FFmpegError(self._procname, self.returncode)

class FFmpegFile(object):
    def __init__(self, filename, exists=True):
        self.filename = filename
        if exists:
            self.__dict__.update(self.get_metadata())

    def get_metadata(self):
        cull_empty = lambda d: dict((k, v) for k, v in d.items() if v not in ('', None))
        want = set('framerate duration width height bitrate framecount'.split())

        # First, try MediaInfo, as it gives better results for many files.
        try:
            meta = cull_empty(self._get_mediainfo_metadata())
            missing = want.difference(meta.keys())
        except InvalidInputError:
            meta = dict()
            missing = want

        if missing:
            # MediaInfo didn't provide all the information we want.
            # Try FFprobe.
            try:
                meta.update(cull_empty(self._get_ffprobe_metadata()))
            except InvalidInputError:
                pass

            still_missing = want.difference(meta.keys())
            for key in still_missing:
                meta[key] = None

        if not meta['framecount'] and meta['duration'] and meta['framerate']:
            # manually calculate the number of frames
            meta['framecount'] = meta['duration'] * meta['framerate']

        return meta

    def _get_mediainfo_metadata(self):
        floatint = lambda x: int(float(x))
        query = {
            'General' : {'VideoCount' : bool},
            'Video' : {
                'FrameRate' : floatint,
                'Width' : int, 'Height' : int,
                'Duration' : int, 'BitRate' : floatint,
                'FrameCount' : int
            }
        }
        info = get_file_metadata(self.filename, **query)
        if not info['General']['VideoCount']:
            raise InvalidInputError(self.filename)

        info = info['Video']
        meta = dict((key.lower(), info[key]) for key in query['Video'].keys())
        if meta.get('bitrate') is not None:
            meta['bitrate'] //= 1000
        if meta.get('duration') is not None:
            meta['duration'] //= 1000
        return meta

    def _get_ffprobe_metadata(self):
        proc = FFmpegSubprocess(['ffprobe', self.filename], stderr=PIPE)
        proc.safe_wait()
        if not proc.successful():
            proc.raise_error()
        stderr = proc.stderr.read()
        width, height = extract_width_and_height(stderr)
        return {
            'framerate' : extract_fps(stderr),
            'duration' : extract_duration(stderr),
            'bitrate' : extract_bitrate(stderr, unavailable=None),
            'width' : width,
            'height' : height
        }

