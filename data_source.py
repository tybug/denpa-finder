from abc import abstractmethod, ABC
import unicodedata
import re

from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup, NavigableString
import requests

# A note on unicode normalization follows. Consider the following two strings:
# a) ポヤッチオ
# b) ポヤッチオ
# They look identical, but they are not. The "first" character in a) is a true
# single character, but the "first" character in b) is actually two characters:
# the character "ホ" followed by a diacritic. These two strings therefore do not
# compare as equal. See for yourself: ``assert "ポヤッチオ" != "ポヤッチオ"``
#
# We can solve this (and other related issues, I believe) by normalizing the
# strings before comparing them. When normalizing boh a), there is no change.
# When normalizing b), the two distinct code points are combined into a single
# character, identical to the first character in a). So the strings are
# equivalent, as desired.
#
# The reason this is desired is fairly obvious, but I'll elaborate just in case:
# there are all kinds of reasons someone may use one form or another of a string
# in an album title or music dump. They look identical, so the user has no way
# of noticing they are using an 'abnormal' form. Our end goal is to get strings
# which are visually identical to be equal. Normalizing realizes this goal.
#
# I will admit to not fully understanding the differences between the four
# normalization forms, but NFKC - decompose by compatibility then recompose by
# canonical equivalence - seems to be what we want.


class Album:
    def __init__(self, title, location, download_url=None):
        self.title = unicodedata.normalize("NFKC", title)
        self.location = location
        self.download_url = download_url

    def contains(self, title):
        title = unicodedata.normalize("NFKC", title)
        return title.lower() in self.title.lower()

    def ratio(self, title):
        title = unicodedata.normalize("NFKC", title)
        return fuzz.partial_ratio(self.title.lower(), title.lower()) / 100

    def __str__(self):
        return (f"Album(title={self.title}, location={self.location}, "
            f"download_url={self.download_url})")
    __repr__ = __str__

    def __hash__(self):
        return hash(self.title)


class AlbumSource(ABC):
    @abstractmethod
    def albums(self):
        pass


# listen, I don't choose the name of the dumps
class RapeTheLolis(AlbumSource):
    URL = "http://denpa.omaera.org/RapeTheLolis_dump.html"

    def albums(self):
        r = requests.get(self.URL)
        r.encoding = "UTF-8"
        soup = BeautifulSoup(r.text, features="lxml")

        albums = []
        for a in soup.find_all("a"):
            album = Album(a.text, self.URL, download_url=a["href"])
            albums.append(album)
        return albums


class SilenceTheDiscord(AlbumSource):
    BASE_URL = "http://135.181.29.38"
    # useful test cases (all of these are legitimate entries in the dump):
    # [**C94**] 領域ZERO - 東方空宴歌-NEVER- [**FLAC+SCANS**]
    # [C97] Baguettes Ensemble - Toho Jazz Connection Vol.6 - (FLAC) (self-rip)
    # {C93] CielArc - 残響のタクティクス (FLAC+log+jpg)
    ALBUM_RE = re.compile(r"^(?:\*+?|{|【|\[|\().+?(?:\*+?】|\]|\)|})(.*)")

    def albums(self):
        albums = []
        for page in ["comiket", "reitaisai", "m3", "misc", "requests"]:
            albums += self._albums_from_page(page)
        return albums

    def _albums_from_page(self, page):
        url = f"{self.BASE_URL}/{page}"
        r = requests.get(url)
        r.encoding = "UTF-8"
        soup = BeautifulSoup(r.text, features="lxml")

        albums = []
        for paragraph in soup.find_all("p"):
            for element in paragraph.children:
                if not isinstance(element, NavigableString):
                    continue
                match = self.ALBUM_RE.match(element)
                if not match:
                    continue
                title = match.group(1).strip()
                # TODO this currently ignores
                # Canoue - イセルディア戦記　暗謀と信義の城楼
                # because the (C95) marker is alone on the line above so it gets
                # parsed as the empty string. We could just take the next line
                # as the title on an empty string, except then we run into
                # trouble in cases like [various formats] which also match our
                # regex and get parsed as the empty string, but are not followed
                # by an album title. That said, false negatives are
                # significantly worse than false positives due to our fuzzy
                # string matching pass at the end, so it's probably worth
                # implementing what I described above.
                if title == "":
                    continue
                album = Album(title, url)
                albums.append(album)
        return albums


class AudioForYou(AlbumSource):
    URL = "https://audioforyou.top/?p=184"
    def albums(self):
        r = requests.get(self.URL)
        r.encoding = "UTF-8"
        soup = BeautifulSoup(r.text, features="lxml")

        albums = []
        for element in soup.select_one(".su-spoiler-content").children:
            if isinstance(element, NavigableString):
                continue
            title = element.text.strip()
            album = Album(title, self.URL)
            albums.append(album)
        return albums
