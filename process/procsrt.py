import codecs
import sys
import csv

from tokenizer import *
from lemmatizer import *
from procchat import *

if len(sys.argv) < 2:
    print "Usage: {0} action_command_csv".format(sys.argv[0])
    quit()

f = codecs.open(sys.argv[1], 'rt')

state = 0
row = []
total = []

ch_reader = csv.reader(f, delimiter = ',')

tk = Tokenizer()
lm = Lemmatizer()

tabbed = [x for x in ch_reader]
lemmed = lemmatize_chat(tabbed, 5, write=True)

f.close()
