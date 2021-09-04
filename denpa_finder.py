from data_source import RapeTheLolis, SilenceTheDiscord, AudioForYou, DenpaGist

class DenpaFinder:
    DATA_SOURCES = [RapeTheLolis(), SilenceTheDiscord(), AudioForYou(),
        DenpaGist()]

    def __init__(self):
        self.albums = []
        for data_source in self.DATA_SOURCES:
            self.albums += data_source.albums()

    def matches(self, query, ratio=0.8):
        ret = []
        for album in self.albums:
            if album.contains(query) or album.ratio(query) >= ratio:
                ret.append(album)
        return ret
