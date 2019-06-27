import codecs
import sys
import csv
from lemmatizer import *
from tokenizer import *


removable_phrases = set(['there we go', 'there you go', 'here we go', 
    'here you go'])

removable_words = set(['is', 'are', 'will', 'oh'])

ignore_signals = '"'

def chatfile_to_tabular(filename, write = False):
    f = codecs.open(filename, 'rt')

    state = 0
    row = []
    total = []
    mem = {}
    fixuser = False

    for e0 in f.readlines():
        e = e0.strip()
        if state == 0:
            if len(e) == 0:
                continue
            assert(e[0] != '-')
            xx = e.split(':')
            if e not in mem:
                mem[e] = 0
            else:
                mem[e] += 1

            if len(xx[-1]) > 2:
                fixuser = True
                user = xx[-1][2:]
                xx[-1] = xx[-1][:2]
            assert(len(xx[-1]) == 2)

            if len(xx) == 2:
                stamp = '00:{0}:{1},{2}'.format(xx[0].zfill(2), xx[1].zfill(2),
                    str(mem[e]).zfill(3))
            elif len(xx) == 3:
                stamp = '{0}:{1}:{2},000'.format(xx[0].zfill(2), xx[1].zfill(2),
                        xx[2].zfill(2), str(mem[e]).zfill(3))
            else:
                print "NO", e
                assert(0)
            row.append(stamp)
            state = 1

            if fixuser:
                fixuser = False
                row.append(user)
                state = 2

        elif state == 1:
            row.append(e)
            state = 2
        elif state == 2:
            if len(e) == 0:
                row.append('__none__')
                total.append(row)
                state = 0
                row = []
            else:
                row.append(e)
                state = 3
        else:
            if len(e) > 0:
                row[2] += ' // ' + e
            else:
                state = 0
                total.append(row)
                row = []

    f.close()

    if write:
        opw = csv.writer(sys.stdout, delimiter=',', quotechar='"', 
            quoting=csv.QUOTE_MINIMAL)

        for e in total:
            opw.writerow(e)

    return total


def lemmatize_chat(tabular, datcol, write = False):

    tk = Tokenizer()
    lm = Lemmatizer()

    result = []

    for e in tabular:
        blah0 = e[datcol].strip().lower()
        for e2 in removable_phrases:
            blah0 = blah0.replace(e2, '')
        blah = []
        for e2 in blah0.split(' '):
            if len(e2) == 0:
                continue
            if e2 in removable_words:
                continue
            blah.append(e2)
        blah = ' '.join(blah)
        tkl = tk.tokenize(blah)
#        if e[2] == '__none__':
#            continue

        lemmed = []
        for ii, e2 in enumerate(tkl):
            if len(e2) < 2:
                continue
            if e2[0] in ignore_signals:
                ret = (1L, e2, 'n', 'n', 1L)
            else:
                ret = lm.lemmatize(e2)
            if ret == None:
                continue
            if ret[2] not in ('n', 'v'):
                continue
            lemmed.append(ret[1] + '+' + ret[2])

        if len(lemmed) == 0:
            continue

        result.append([e[0], e[1], ' '.join(lemmed), blah0])
#        csv_writer.writerow([e[0], e[1], ' '.join(lemmed)])
 
    if write: 
        opw = csv.writer(sys.stdout, delimiter=',', quotechar='"', 
            quoting=csv.QUOTE_MINIMAL)
        for e in result:
            opw.writerow(e)

    return result

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "Usage: {0} chatfile".format(sys.argv[0])
        quit()

    tab = chatfile_to_tabular(sys.argv[1])
    lemmed = lemmatize_chat(tab, 2, write=True)
#    print lemmed
