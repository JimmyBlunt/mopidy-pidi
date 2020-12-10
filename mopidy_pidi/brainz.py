"""
Musicbrainz related functions.
"""
import base64
import logging
import os
import time
from threading import Thread

import musicbrainzngs as mus

from .__init__ import __version__

logger = logging.getLogger(__name__)


class Brainz:
    def __init__(self, cache_dir):
        """Initialize musicbrainz."""
        mus.set_useragent(
            "python-pidi: A cover art daemon.",
            __version__,
            "https://github.com/pimoroni/mopidy-pidi",
        )

        self._cache_dir = cache_dir
        self._default_filename = os.path.join(self._cache_dir, "__default.jpg")

        self.save_album_art(self.get_default_album_art(), self._default_filename)

    def get_album_art(self, artist, album, callback=None):
        if artist is None or album is None or artist == "" or album == "":
            if callback is not None:
                return callback(self._default_filename)
            return self._default_filename

        file_name = self.get_cache_file_name(f"{artist}_{album}")
        logger.info("BRAINZ::get_album-art: get_cached_file_name:(fartist_album" + str(file_name))
        if os.path.isfile(file_name):
            # If a cached file already exists, use it!
            if callback is not None:
                return callback(file_name)
            return file_name

        file_name1 = f"{artist}_{album}.jpg".replace("/", "")
        file_name1 = "/var/lib/mopidy/pidi/"+file_name1
        logger.info("BRAINZ:get_album-art: file_name1:" + str(file_name1))
        
        if os.path.isfile(file_name):
           if callback is not None:
               return callback(file_name)
           return file_name

        if callback is not None:

            def async_request_album_art(self, artist, album, file_name, callback):
                album_art = self.request_album_art(artist, album)

                if album_art is None:
                    # If the MusicBrainz request fails, cache the default
                    # art using this filename.
                    self.save_album_art(self.get_default_album_art(), file_name)
                    return callback(file_name)

                self.save_album_art(album_art, file_name)

                return callback(file_name)

            t_album_art = Thread(
                target=async_request_album_art,
                args=(self, artist, album, file_name, callback),
            )
            t_album_art.start()
            return t_album_art

        else:
            album_art = self.request_album_art(artist, album)

            if album_art is None:
                # If the MusicBrainz request fails, cache the default
                # art using this filename.
                self.save_album_art(self.get_default_album_art(), file_name)
                return file_name

            self.save_album_art(album_art, file_name)

            return file_name




#            album_art = self.request_album_art(artist, album)
#
#            if album_art is None:
#
#                file_name = f"{album}".jpg
#                logger.info("BRAINZ::get_album-art: BrainzRequestFailed-try-cleartexfile.f{album}).jpg" + str(file_name))
#                if os.path.isfile(file_name):
#                   # If a cached file already exists, use it!
#                   if callback is not None:
#                      return callback(file_name)
#                   return file_name
#                file_name1 = f"{album}.jpg".replace("/", "")
#                file_name1 =  "/var/lib/mopidy/pidi/"+file_name1
#                logger.info("BRAINZ:get_album-art: onlyalbumfile_name1:" + str(file_name1))
#
#                if os.path.isfile(file_name1):
#                   if callback is not None:
#                      return callback(file_name1)
#                   return file_name1
#                if album_art is None:
                # If the MusicBrainz request fails, cache the default
                # art using this filename.
 #                  self.save_album_art(self.get_default_album_art(), file_name)
 #                  return file_name
              # If the MusicBrainz request fails, cache the default
#               # art using this filename.
#                  self.save_album_art(self.get_default_album_art(), file_name)#
#                  return file_name
#            self.save_album_art(album_art, file_name)
#            return file_name

    def save_album_art(self, data, output_file):
        with open(output_file, "wb") as f:
            f.write(data)

    def request_album_art(self, artist, album, size=500, retry_delay=5, retries=5):
        """Download the cover art."""
        try:
            data = mus.search_releases(artist=artist, release=album, limit=1)
            release_id = data["release-list"][0]["release-group"]["id"]
            logger.info("mopidy-pidi: musicbrainz using release-id: {release_id}")

            return mus.get_release_group_image_front(release_id, size=size)

        except mus.NetworkError:
            if retries == 0:
                # raise mus.NetworkError("Failure connecting to MusicBrainz.org")
                return None
            logger.info(
                f"mopidy-pidi: musicbrainz retrying download. {retries} retries left!"
            )
            time.sleep(retry_delay)
            self.request_album_art(artist, album, size=size, retries=retries - 1)

        except mus.ResponseError:
            logger.info(
                f"mopidy-pidi: musicbrainz couldn't find album art for {artist} - {album}"
            )
            return None

    def get_cache_file_name(self, file_name):
        file_name = file_name.encode("utf-8")
        file_name = base64.b64encode(file_name)
        if type(file_name) is bytes:
            file_name = file_name.decode("utf-8")
        # Ruh roh, / is a vaild Base64 character
        # but also a valid UNIX path separator!
        file_name = file_name.replace("/", "-")
        file_name = f"{file_name}.jpg"

        return os.path.join(self._cache_dir, file_name)

    def get_default_album_art(self):
        """Return binary version of default album art."""
        return base64.b64decode(
            """
/9j/4AAQSkZJRgABAgEAlgCWAAD//gASTEVBRFRPT0xTIHYyMC4wAP/bAIQABQUFCAUIDAcHDAwJCQkMDQwMDAwNDQ0NDQ0NDQ0ND
Q0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQEFCAgKBwoMBwcMDQwKDA0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ
0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0N/8QBogAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoLAQADAQEBAQEBAQEBAAAAAAAAAQI
DBAUGBwgJCgsQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkq
NDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw
8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+hEAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFE
KRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiIm
KkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/8AAEQgAvgENAwEi
AAIRAQMRAf/aAAwDAQACEQMRAD8A+m9UuZo7p1R3VRtwAxAHyr2BqiLu4P8Ay0k/77b/ABqfVh/pkn/Af/QFquiV6KtyrTovyPz6r
Kcq9WKlKyqT6v8AmYk99cQRmTfNIR0VGYt9fp+Nczc65qL8bpYk+rk/jmuxWOpxFU6J7I9zCT9lbmhzy/mlKX4J3R5rLqLSLtkRHY
D777t5z7lh/KqwuW2eWyodo67QWHsG6j8jXZeJYVS2VgoBEg5wAeQeOB/M1x1latezCBRw3LEdh3rdONnK1kmfUQn7SPPt5XESdIi
GEa5U55LYP1GRnPfrXaWuvG8bYJHjc9E3sB/wHnH4dfarP/CP2S9Ih/30/wD8VTG0GzP/ACz6f7T/AKfMMVlKcXsjjqTp1VaXOrap
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
#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"""
        )
'''















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"""
        )	

        return base64.b64decode(
            """
iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAMAAAAM7l6QAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFn
ZVJlYWR5ccllPAAAAMBQTFRFBHwvBSl8d04DCQ99egJLfAMzejQGcGoAAGZ6AHN3N3wBSHwBKXwDAHlp
NQF9AHtXAFV7VwB7HgN9B30aG30FXncAAXtERwB8fQMbZQB5AUF8fRsHQ04rfQgLFlZTVzgteABiZ14F
agNiAmpoF3kaLVU4V1QVYhdFLkZIQy1MFWc/biYkKSVpLWUmLjVYcQBzJHMbeRQiBWxZBlxnOmkXDn0M
WAdnGhd5FkBlSRZfCk1rO3MMTmwJCm5FQgtwMhJydzVfDgAAAYtJREFUeNpUzeligjAQBOCNgFcVFVRQ
FC3gUU/Uingg7/9W3U1CpJOf38wGGpQ2ptPpDIcAYNv29Xrt9/utVqsJXBsfLmmzKbiYy3WZ6/XC1fyj
X8iiIOZQsFDBvFBct+1I6BcGuvUuedgIwzOfR9dI6QC6FF4I2+dsmEEURVIHA+RxVzZwfs4gi+JW3Hwi
ch5juF8ul/CcbTZxHD+ffFqwrGDB32z2+9/n6/VCqw1qwMZMFh6Ph+/7C2RUJAowGWqlqb9eLCa/y2/M
f2YsZWl6WK8nk+VSOTBN05iGemO73e5w+JnNZpVlRQYIKTcM+g/xtiq1BloR5Dy/3++r7ba6rWLkmmLd
LCvP8zfqCp0zNYgtepZlmu93kiCfTifP87iDNK5OkiSBbpyEe1WPs0DTdJxeEAQr3TCUgyXUQnR6ySgI
dJy7rjclV8y3PdS5jm647nRKDVBIOjoSG4KpAOpfB3V0nM/LjmyapXHBriscylrwx0FpiQ11Hf6PyXX5
ORWAoxqr44Y4/ifAAPd/TAMIg8r1AAAAAElFTkSuQmCC"""
        )	
'''
