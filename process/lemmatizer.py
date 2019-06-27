import atexit
import MySQLdb

vowels = set([x for x in 'aeiou'])
consonants = set([x for x in 'bcdfghjklmnpqrstvwxyz'])

#ignore_signals = '"'

def ends_in_double_consonant(s):
    if len(s) < 2:
        return False
    if s[-1] not in consonants:
        return False
    if s[-2] not in consonants:
        return False
    if s[-1] != s[-1]:
        return False
    return True

_default_endings = {
    'ily': [([], 'y', 'a', 'r')],
    'ly': [([], '', 'a', 'r')],
    'ing': [([ends_in_double_consonant], '-', 'v', 'n'),
        ([], 'e', 'v', 'n'), ([], '', 'v', 'n')],
    'es': [([], '', 'v', 'v'), ([], '', 'n', 'n')],
    'ies': [([], 'y', 'v', 'v'), ([], 'y', 'n', 'n')],
    's': [([], '', 'v', 'v'), ([], '', 'n', 'n')]
}

auxs = {
    'are': (1, 'be', 'v', 'v', 1),
    'is': (1, 'be', 'v', 'v', 1),
    'was': (1, 'be', 'v', 'v', 1),
    'were': (1, 'be', 'v', 'v', 1),
    'has': (1, 'be', 'v', 'v', 1),
    'my': (1, 'my', 'p', 'p', 1),
    'your': (1, 'my', 'p', 'p', 1),
    'his': (1, 'my', 'p', 'p', 1),
    'her': (1, 'my', 'p', 'p', 1),
    'our': (1, 'my', 'p', 'p', 1),
    'their': (1, 'my', 'p', 'p', 1), #mine is tricky
    'yours': (1, 'my', 'p', 'p', 1),
    'hers': (1, 'my', 'p', 'p', 1),
    'ours': (1, 'my', 'p', 'p', 1),
    'their': (1, 'my', 'p', 'p', 1),
}

reserved_words = {
    'left': (1, 'left', 'n', 'n', 1),
    'right': (1, 'right', 'n', 'n', 1),
}

class Lemmatizer:
    def __init__(self, endings = _default_endings, 
        dbinfo = ('localhost', 'wordnet', 'root', '')):

        self.endings = endings
        self.ending_lengths = set([len(k) for k in endings.keys()])
        self.dbhost = dbinfo[0]
        self.dbname = dbinfo[1]
        self.dbuser = dbinfo[2]
        self.dbpass = dbinfo[3]

        self.conn = MySQLdb.connect(dbinfo[0], dbinfo[2], dbinfo[3], dbinfo[1])
        self.cursor = self.conn.cursor()

        #FIXME add wordnet link
        atexit.register(self.destructor)

    def destructor(self):
        self.conn.close()

    def returnCandidates(self, s):
        el = [s[-e:].lower() for e in self.ending_lengths if len(s) >= e]
        result = [(s, '', '', '')]

        for e in el:
            if e in self.endings:
                for e2 in self.endings[e]:
                    s2 = s[:-len(e)]
                    if not all([x(s2) for x in e2[0]]):
                        continue


                    #so we made it, now perform the action
                    s2 = s[:-len(e)]
                    for k in e2[1]:
                        if k == '-':
                            s2 = s2[:-1]
                        else:
                            s2 += k

                    result.append((s2, e, e2[2], e2[3]))

        return result

    def doQuery(self, cands):
        raw = cands[0][0]

        #create mappings
        mp = {}
        for e in cands[1:]:
            assert((e[0], e[2]) not in mp)
            mp[(e[0], e[2])] = e[3]

        baseq = "select senses.wordid, senses.synsetid, lemma, pos, tagcount, lemma='{0}' from senses, words, synsets where senses.synsetid=synsets.synsetid and senses.wordid=words.wordid".format(MySQLdb.escape_string(raw))
        ql = []
        for e in cands:
            if e[2]:
                ql.append("(lemma='{0}' and pos='{1}')".format(
                    MySQLdb.escape_string(e[0]), e[2]))
            else:
                ql.append("(lemma='{0}')".format(MySQLdb.escape_string(e[0])))
        q = baseq + ' and (' +  ' or '.join(ql) + ')'
        self.cursor.execute(q)
       
        counter = {}
        poscount = {}

        for e in self.cursor.fetchall():
            mapped_pos = e[3]
            if (e[2], e[3]) in mp:
                mapped_pos = mp[(e[2], e[3])]

            if mapped_pos not in poscount:
                poscount[mapped_pos] = 0
            poscount[mapped_pos] += e[4]

            key = (e[2], mapped_pos, e[3], e[5])
            if key not in counter:
                counter[key] = 0
            counter[key] += e[4]

           

        sorter = list(reversed(sorted([(v, k[0], k[1], k[2], k[3]) for
            k, v in counter.items()])))
        return sorter, list(reversed(sorted((v, k) 
            for k, v in poscount.items())))


    def lemmatize(self, s, ignore_auxs = True):
        if s in auxs:
            if ignore_auxs:
                return None
            return auxs[s]

        if s in reserved_words:
            return reserved_words[s]

        if len(s) < 2:
            return (1L, s, '0', '0', 1L)

#        if s[0] in ignore_signals:
#            return (1L, s, 'n', 'n', 1L)

        #1 return possible connections:
        cands = self.returnCandidates(s)


        lemmed, posses = self.doQuery(cands)

        if len(posses) == 0:
            return None

        xl = [x for x in lemmed if x[2] == posses[0][1]]
        return xl[0]
            

if __name__ == "__main__":
    import sys
    from tokenizer import *
    if len(sys.argv) < 2:
        print "Usage: {0} sentence".format(sys.argv[0])
        quit()

    tk = Tokenizer()
    tkl = tk.tokenize(' '.join(sys.argv[1:]))
    print tkl
    lm = Lemmatizer()
    for e in tkl:
        print lm.lemmatize(e)
