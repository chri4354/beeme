import re

_default_separators = '\'.,?!;: \t()'
_default_quotes = '"'
_default_separators = set([x for x in _default_separators])

_default_abbrevs = {
    "'": {'m': 'am', 's': "'s", "'d": "had", "'ll": "will", "'ve": "have",
        "'re": "are"},
    "couldn": {"'": {'t': "could not"}},
    "didn": {"'": {'t': "did not"}},
    "don": {"'": {'t': "do not"}},
    "doesn": {"'": {'t': "does not"}},
    "shouldn": {"'": {'t': "should not"}},
    "can": {"'": {'t': "cannot"}},
    "won": {"'": {'t': "will not"}},
    "shan": {"'": {'t': "shall not"}},
    "wouldn": {"'": {'t': "would not"}},
    "haven": {"'": {'t': "have not"}},
    "hasn": {"'": {'t': "has not"}},
}

class Tokenizer:
    def __init__(self, separators = _default_separators,
        quotes = _default_quotes):
        self.separators = separators
        self.abbrevs = _default_abbrevs
        self.quotes = quotes

    def deep_lookup(self, dct, hist, key):
        cursor = dct
        for e in hist:
            if e in cursor:
                cursor = cursor[e]

        if key in cursor:
            return cursor[key]

        return None


    def resolve_intervals(self, intervals):
        coverage = set([])
        okay = []
        std = sorted(intervals)

        for e in std:
            if e[0] not in coverage:
                okay.append(e)
                coverage.update((range(e[0], e[1] + 1)))
        return okay                


    def deabbreviate(self, l):
        prelim = []
        mem = []
        for i, e in enumerate(l):
            print "Token {0}: {1}".format(i, e), mem
            oldmem = mem
            mem = []
            #1 check old ones
            for e2 in oldmem:
                dl = self.deep_lookup(self.abbrevs, e2[1], e)
                if dl:
                    if type(dl) == dict:
                        el = (e2[0], e2[1] + [e])
                        mem.append(el)

                    elif type(dl) == str:
                        prelim.append((e2[0], i, dl))

                    else:
                        assert(0)
                print "\t", e2, dl
                pass
            if e in self.abbrevs:
                val = self.abbrevs[e]
                if type(val) == dict:
                    mem.append((i, [e]))
                elif type(val) == str:
                    prelim.append((i, i, val))
                else:
                    assert(0)

        resolved = self.resolve_intervals(prelim)
                            
        #and finally, substitute
        for elt in reversed(resolved): #note: resolved is already sorted!
            tail = []
            if elt[1] < len(l):
                tail = l[elt[1] + 1:]
            head = l[:elt[0]]
            l = head + elt[2].split(' ') + tail
        return l

    def collapse_quotes(self, s):
        result = s[:]
        for e in self.quotes:
            result = result.split(e)
            for j, e2 in enumerate(result):
                if j % 2 == 1:
#                    result[j] = ''.join([x.title() for x in e2.split(' ')])
                    result[j] = ''.join([x for x in e2.split(' ')]).lower()
            result = e.join(result)
        return result


    def tokenize(self, s, drop_separators=False, deabbreviate = False,
            drop_whitespaces=True, collapse_quotes=True):
        prelims = []
        curs = []

        if collapse_quotes:
            s = self.collapse_quotes(s)

        for e in s:
            if e not in self.separators:
                curs.append(e)
            else:
                if len(curs) > 0:
                    prelims.append(''.join(curs))

                if e in [' ', '\t']:
                    if not drop_whitespaces:
                        prelims.append(e)
                elif not drop_separators:
                    prelims.append(e)
                curs = []

        if len(curs) > 0: #so last token is not a separator
            prelims.append(''.join(curs))

        if deabbreviate:
            prelims = self.deabbreviate(prelims)

        return prelims            

if __name__ == "__main__":
    import sys
    tk = Tokenizer()
    tr = tk.tokenize(sys.argv[1], deabbreviate=True)
    print tr
