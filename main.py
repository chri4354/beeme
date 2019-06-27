import codecs
import csv
import sys

from testcalcs import *

import matplotlib.pyplot as plt
from base import *
from segstatter import *

"""
Some settings: test to perform on segments, operator delay.
"""
sctests = [('full', full_test), ('loose_full', loose_full_test),
    ('b_o_w', bagofwords1), ('indicator', indicator_test),
    ('moment', moment_test), ('decay', decay_test)]

operator_delay = 1000

"""
The chat evals contain a classification related to the Winter and Neuro inputs.
The classification aims to determine, which segments are usable.
"""
chatevals = {
    'winter': {
        'good': set([0, 1, 3, 5, 6, 8, 10, 12, 13, 14, 18, 19, 32, 34, 42, 43,
    45, 47, 48, 49, 50, 52, 54, 64, 66, 67, 72, 74, 75, 76, 83, 84, 85]),

        'notsure': set([2, 7, 9, 11, 17, 21, 26,38, 51, 53, 78, 79, 90]),

        'bad': set([4, 15, 16, 22, 23, 25, 27, 28, 29, 30, 31, 33, 35, 36, 37, 39,
            40, 44, 46, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 68, 69, 70, 71, 73,
            77, 80, 81, 82, 86, 87, 88, 89, 91])
    },
    'neuro': {
        'good': set([13,14,19,22,36,38,39,42,47,58,66,67,71,72,73,74,75,81,84]),
        'notsure': set([4,23,57,76]),
        'bad': set([0,1,2,3,5,6,7,8,9,10,11,12,15,16,17,18,20,21,24,25,26,27,
            28,29,30,31,32,33,34,35,37,40,41,43,44,45,46,48,49,50,51,52,53,54,
            55,56,59,60,61,62,63,64,65,68,69,70,77,78,79,80,82,83]),
        }
}

filter_out = ['bad', 'notsure']

"""
Determine is the segment is to be considered for processing. This is based
on the manual evaluation contained in chatevals.
"""
def segment_ok(seg, fltr, scenario):
    for e in fltr:
        if seg.command.ctr in chatevals[scenario][e]:
            return False
    return True

"""
This function extracts all relevant statistics from a segment.
memvec is designed to be used for matching, statvec for analysis / charting.
"""
def summarize_segments(segments):
    #initialize the result variables
    memvec = []
    statvec = []

    for i1, e in enumerate(segments):
        #filter out initial part of the segment
        e.filter((0.4, 1))

        #prepare and store segment stats for analysis / plotting
        mem = stat_segment(e)
        rr = calcsegstats(e, mem)

        memvec.append(mem)
        statvec.append(rr)

    return memvec, statvec

"""
Segments' chat summary information (memvec) matched against their
action commands using various tests.
"""
def match_segments(segments, memvec, tests, scenario_name):
    scores = {}
    #now 
    for i1, e in enumerate(segments):
        if len(e.entries) == 0:
            continue

        if not segment_ok(e, filter_out, scenario_name):
            continue

        #the following line is useful for studying the problem, but should
        #be commented out when doing online processing.

#        e.filter((0.4, 1))
        tkl0 = e.command.command.lower().split(' ')
        tkl = []
        oktoks = []
        for e2 in tkl0:
            print e2, tkl0
            if e2.find('+') == -1: #indicates a lemmatization error
                print "AAA", e2, tkl0
                quit()
            ll = e2.split('+')
            if ll[0] != '' and ll[1] in ['n', 'v']:
                tkl.append(e2)
                oktoks.append(ll[0])
        proc_cmd = ' '.join(oktoks)

        #print what needs printing
        print "\n=================\nSEGMENT", e.command, '|', \
            proc_cmd
        print "\t", memvec[i1]['n'][:5] 
        print "\t", memvec[i1]['v'][:5] 
        print "\t", memvec[i1]['t'][:5] 
        calc_scores(proc_cmd, tests, memvec[i1], scores, e.command)
        if moment_test(proc_cmd, memvec[i1], tuple2int(e.command.timestamp)):
            e.mlclass = 1
        for i2, e2 in enumerate(memvec[i1]['t'][:5]):
            print "\t", e2
#            plt.plot(e2[2], range(len(e2[2])), label='kax{0}'.format(i2))

    print scores

"""
Plotting. To be refined.
"""
def plot_results(segments, statvec):
    reskeys = statvec[0].keys()
    for e in reskeys:
        print "PLOT FOR KEY {0}".format(e)
        good = [x[e] for i, x in enumerate(statvec) if segments[i].mlclass==1]
        bad = [x[e] for i, x in enumerate(statvec) if segments[i].mlclass==0] #use for unfiltered
        ax1=plt.subplot(2,1,1)
        plt.xlabel('xx')
#        plt.xticks([rangie(10)]), plt.yticks([])
        plt.grid=True
        plt.title('good for {0}'.format(e))
        plt.hist(good, bins=30)

        ax2=plt.subplot(2,1,2, sharex=ax1)
#        plt.xticks([]), plt.yticks([])
        plt.title('bad for {0}'.format(e))
        plt.grid=True
        plt.hist(bad, bins=30)
        plt.show()
        
"""
This function provides a one-stop shopping option for all required 
functionality.
"""
def doall(srtf, chatf, scenario, doplot):

    timeline = read_sources(srtf, chatf)
    segments = build_segments(timeline, operator_delay)

    memvec, statvec = summarize_segments(segments)

    match_segments(segments, memvec, sctests, scenario)
   
    if doplot:
        plot_results(segments, statvec)

if __name__ == "__main__":

    if len(sys.argv) < 4:
        print "Usage: {0} str_csv chat_csv actor_name".format(sys.argv[0])
        quit()

    doall(sys.argv[1], sys.argv[2], sys.argv[3], 0)



