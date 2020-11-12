from collections import defaultdict
from operator import itemgetter
from random import shuffle

import troi
from troi import PipelineError, Recording


class ArtistCreditFilterElement(troi.Element):
    '''
        Remove recordings if they do or do not belong to a given list of artists.
    '''

    def __init__(self, artist_credit_ids, include=False):
        '''
            Filter a list of Recordings based on their artist_credit_id.
            The default behaviour is to exclude the artists given, but if
            include=True then only the artists in the given list pass
            the filter. Throws PipelineError is not all recordings have
            artist_credit_ids set.
        '''
        super().__init__()
        self.artist_credit_ids = artist_credit_ids
        self.include = include

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]

        ac_index = {}
        for ac in self.artist_credit_ids:
            try:
                ac_index[ac] = 1
            except KeyError:
                raise PipelineError(self.__name__ + " needs to have all input recordings to have artist.artist_credit_id defined!")

        results = []
        for r in recordings:
            if not r.artist or not r.artist.artist_credit_id:
                self.debug("recording %s has not artist credit id" % (r.mbid))
                continue

            if self.include:
                if r.artist.artist_credit_id in ac_index:
                    results.append(r)
            else:
                if r.artist.artist_credit_id not in ac_index:
                    results.append(r)

        return results


class ArtistCreditLimiterElement(troi.Element):

    def __init__(self, count=2, exclude_lower_ranked=True):
        '''
            This element examines there passed in recordings and if the count of
            recordings by any one artists exceeds the given limit, excessive recordigns
            are removed. If the flag exclude_lower_ranked is True, then the lowest
            ranked recordings are removed, otherwise the highest ranked recordings
            are removed. Throws PipelineError is not all recordings have
            artist_credit_ids set.
        '''
        troi.Element.__init__(self)
        self.count = count
        self.exclude_lower_ranked = exclude_lower_ranked

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]
        ac_index = defaultdict(list)
        all_have_rankings = True
        for rec in recordings:
            try:
                ac_index[rec.artist.artist_credit_id].append((rec.mbid, rec.ranking))
                if rec.ranking is None:
                    all_have_rankings = False
            except KeyError:
                raise PipelineError(self.__name__ + " needs to have all input recordings to have artist.artist_credit_id defined!")

        for key in ac_index:
            if all_have_rankings:
                ac_index[key] = sorted(ac_index[key], key=itemgetter(1), reverse=self.exclude_lower_ranked)
            else:
                shuffle(ac_index[key])
            ac_index[key] = ac_index[key][:self.count]

        pass_recs = []
        for key in ac_index:
            for mbid, ranking in ac_index[key]:
                pass_recs.append(mbid)

        results = []
        for r in recordings:
            if r.mbid in pass_recs:
                results.append(r)

        return results


class DuplicateRecordingFilterElement(troi.Element):
    """This Element takes a list of recordings and removes any duplicate recordings
    based on the recording's MBID, preserving the input order.
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):
        recordings = inputs[0]
        output = []
        seen = set()
        for rec in recordings:
            if rec.mbid not in seen:
                seen.add(rec.mbid)
                output.append(rec)

        return output


class ConsecutiveRecordingFilterElement(troi.Element):
    """This Element takes a list of recordings and removes consecutive duplicate recordings
    based on the recording's MBID

    For example, a sequence A, A, A, B, B, A, C will be reduced to A, B, A, C
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):
        recordings = inputs[0]
        output = []
        last_mbid = None
        for rec in recordings:
            if rec.mbid != last_mbid:
                output.append(rec)
            last_mbid = rec.mbid

        return output


class EmptyRecordingFilterElement(troi.Element):
    """This Element takes a list of recordings and removes ones that have an empty name
    or artist.
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):
        recordings = inputs[0]
        output = []
        for rec in recordings:
            if rec.name is None or (rec.artist and rec.artist.name is None):
                if debug:
                    print(f"recording {rec.mbid} has no metadata, filtering")
            else:
                output.append(rec)

        return output


class YearRangeFilterElement(troi.Element):
    '''
        Remove/keep recordings if they do or do not belong in a range of years
    '''

    def __init__(self, start_year, end_year, inverse=False):
        '''
            Filter a list of Recordings based on their year -- the year must be between
            start_year and end_year, otherwise the recording will be filtered out.
            If inverse=True, then keep all Recordings that do no fit into the given year
            range.
        '''
        troi.Element.__init__(self)
        self.start_year = start_year
        self.end_year = end_year
        self.inverse = inverse

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):

        recordings = inputs[0]

        results = []
        for r in recordings:
            if not r.year:
                continue

            if self.inverse:
                if r.year < self.start_year or r.year > self.end_year:
                    results.append(r)
            else:
                if r.year >= self.start_year and r.year <= self.end_year:
                    results.append(r)

        return results
