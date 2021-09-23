from denpa_finder.data_source import (RapeTheLolis, SilenceTheDiscord,
    AudioForYou, DenpaGist)
from denpa_finder.query import Q


class DenpaFinder:
    DATA_SOURCES = [RapeTheLolis(), SilenceTheDiscord(), AudioForYou(),
        DenpaGist()]

    def __init__(self):
        self.albums = []
        for data_source in self.DATA_SOURCES:
            self.albums += data_source.albums

    def refresh(self):
        for data_source in self.DATA_SOURCES:
            data_source.refresh()

    def matches(self, q, ratio=0.8):
        if isinstance(q, str):
            q = Q(q)

        ret = []
        for album in self.albums:
            assignment = {}
            for query in q.queries:
                is_match = album.contains(query) or album.ratio(query) >= ratio
                assignment[query] = is_match
            if q(assignment):
                ret.append(album)
        return ret