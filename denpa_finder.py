from data_source import RapeTheLolis, SilenceTheDiscord, AudioForYou

class DenpaFinder:
    DATA_SOURCES = [RapeTheLolis(), SilenceTheDiscord(), AudioForYou()]
    def __init__(self):
        self.albums = []
        for data_source in self.DATA_SOURCES:
            self.albums += data_source.albums()

    def perfect_matches(self, query):
        ret = []
        for album in self.albums:
            if album.contains(query):
                ret.append(album)
        return ret

    def good_matches(self, query, ratio=0.8):
        good_matches = []

        for album in self.albums:
            if album.ratio(query) >= ratio:
                good_matches.append(album)
        return good_matches

df = DenpaFinder()

print(df.perfect_matches("EVERYTOON"))
# print(df.good_matches("T★GIRLS", ratio=0.4))
