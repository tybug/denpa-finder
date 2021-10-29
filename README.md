# Denpa Finder

Searches several denpa / jcore dumps (called "data sources") for albums matching a certain query.

### Current Data Sources

* RTL
* Silence The Discord (all pages, even /requests): <http://135.181.29.38>
* Audio For You: <https://audioforyou.top/?p=184>
* Denpa Gist: <https://gist.github.com/dnpcllctns/f79394cd283ee30834ee6e4bb484b502>

### Installation

```python
git clone https://github.com/tybug/denpa-finder
cd denpa-finder
pip install -e .
```

### Usage

Basic usage:

```python
import pprint
from denpa_finder import DenpaFinder

df = DenpaFinder()
matches = df.matches("ななひら")
pprint.pprint(matches, indent=4)
```

#### Fuzzy Matching

Denpa Finder performs fuzzy matching on the search string by default. This means that an album with a title one letter off from your search query will still be returned in the results. This is convenient for typos or weird characters in an artist's name which some data sources write differently (P*light vs P＊light, for instance).

If you'd like to adust the ratio at which fuzzy matches are made, pass a float between `0` and `1` to the `ratio` parameter of `df.matches` (the default is `0.8`). If you'd like to disable fuzzy matching completely, pass `ratio=1`.

```python
# more fuzzy matches will be returned (less exact ones)
matches = df.matches("ななひら", ratio=0.7)
# less fuzzy matches will be returned
matches = df.matches("ななひら", ratio=0.9)
# no fuzzy matches will be returned, only exact ones
matches = df.matches("ななひら", ratio=1)
```

#### Complex Queries

I often find myself needing to express a more complex query than just "search for this string". For that, denpa finder provides the `Q` (short for "query") object, which can be AND'd, OR'd, and NOT'd:

```python
from denpa_finder import DenpaFinder, Q

df = DenpaFinder()
# anything that matches either "camellia" or "かめりあ"
q1 = Q("camellia") | Q("かめりあ")
# anything that matches "haru" and "ama" and "nia".
# used this recently when I wanted to find albums by
# haru＊ama＊nia but wanted to avoid getting tripped up
# by some people using weird asterisks for the artist name
q2 = Q("haru") & Q("ama") & Q("nia")
# albums by camellia, but not with nanahira
q3 = (Q("camellia") | Q("かめりあ")) & (~(Q("nanahira") | Q("ななひら")))

matches1 = df.matches(q1)
matches2 = df.matches(q2)
matches3 = df.matches(q3)
```

#### Caching

DenpaFinder caches scraped albums from each data source, since loading and parsing the html is the majority of the cost of matching a query. If you'd like to refresh the caches, call `df.refresh()`.
