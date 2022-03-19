from abc import abstractmethod, ABC
import unicodedata
import re
from pathlib import Path
import pickle
import codecs

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
    def __init__(self, key):
        self.albums = None

        self.data_file = Path(__file__).parent / f"{key}.pickle"
        if self.data_file.exists():
            with open(self.data_file, "rb") as f:
                self.albums = pickle.load(f)
        else:
            self.refresh()

    @abstractmethod
    def retrieve_albums(self):
        pass

    def refresh(self):
        self.albums = self.retrieve_albums()
        self.save()

    def save(self):
        with open(self.data_file, "wb") as f:
            pickle.dump(self.albums, f)


encoded = codecs.encode("EncrGurYbyvf_qhzc", "rot-13")
class RTL(AlbumSource):
    URL = f"http://denpa.omaera.org/{encoded}.html"

    def __init__(self):
        super().__init__("rtl")

    def retrieve_albums(self):
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
    # TODO this regex currently fails on:
    # Canoue - イセルディア戦記　暗謀と信義の城楼
    ALBUM_RE = re.compile(r"^(?:\*+?|{|【|\[|\().+?(?:\*+?】|\]|\)|})(.*)")
    DOWNLOAD_URL_RE = re.compile(r"(?:DL|DOWNLOAD).*?:(.*)")

    def __init__(self):
        super().__init__("silence_the_discord")

    def retrieve_albums(self):
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
            title = None
            download_url = None

            for element in paragraph.children:
                if not isinstance(element, NavigableString):
                    continue

                title = title or self._title_from_element(element)
                download_url = (
                    download_url or self._download_url_from_element(element)
                )

            if title:
                album = Album(title, url, download_url)
                albums.append(album)
        return albums

    def _title_from_element(self, element):
        match = self.ALBUM_RE.match(element)
        if not match:
            return None

        title = match.group(1).strip()
        if title == "":
            return None

        return title

    def _download_url_from_element(self, element):
        # TODO also look for mega.nz or mediafire urls and fallback to those.
        # download urls have some weird formats, eg
        #
        # DL:
        # https://mega.nz/#!D3hjAaoa!MI404Xpj0SsLkMb6HLV3ggqvzb0_BB4HMb7uAvKfiQE
        #
        # or
        #
        # [FLAC] DL:https://mega.nz/#F!3U8nDBZC!zDSI8pjKeoUQm-z2FwntAg
        # [320kbps]: https://mega.nz/#F!DMdXHAyA!JeB4NnptfEW7NVgq4fhfBQ XFD: https://youtu.be/Y33WrCSpbts
        #
        match = self.DOWNLOAD_URL_RE.match(element)
        if not match:
            return None

        download_url = match.group(1).strip()
        if download_url == "":
            return None

        return download_url


class AudioForYou(AlbumSource):
    URL = "https://audioforyou.top/j-core-compilation/"

    def __init__(self):
        super().__init__("audio_for_you")

    def retrieve_albums(self):
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

class DenpaGist(AlbumSource):
    URL = "https://gist.github.com/dnpcllctns/f79394cd283ee30834ee6e4bb484b502"
    URL_RAW = "https://gist.githubusercontent.com/dnpcllctns/f79394cd283ee30834ee6e4bb484b502/raw"
    DOWNLOAD_RE = re.compile(r"(.*?)\s*?-\s*?(https://mega\.nz.*)")

    def __init__(self):
        super().__init__("denpa_gist")

    def retrieve_albums(self):
        r = requests.get(self.URL_RAW)
        r.encoding = "UTF-8"
        lines = r.text.split("\n")
        lines = iter(lines)

        line = next(lines)
        while "June - December 2018" not in line:
            line = next(lines)

        albums = []
        for line in lines:
            match = self.DOWNLOAD_RE.search(line)

            title = line
            download_url = None
            if match:
                title = match.group(1)
                download_url = match.group(2)

            album = Album(title, self.URL, download_url)
            albums.append(album)
        return albums
