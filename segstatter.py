from base import *
import numpy as np

"""
These functions compute segment statistics for various charting purposes.
"""

"""
This function computes summary segment statistics -- number of words, unique
    words, segment lengths, variances etc.
These statistics help us formulate a better idea of what user commands look
    like.
"""
def overall1(seg, result):
    result['nentries'] = len(seg.entries)
    result['nseconds'] = (tuple2int(seg.end_time) - 
        tuple2int(seg.start_time)) // 1000
    lens = []        
    for e in seg.entries:
        lens.append(len(e.command.split(' ')))
    if len(seg.entries) == 0:

        result['average_len'] = 0
        result['std_len'] = 0
        result['rel_std_len'] = 0
    else:
        result['average_len'] = int(100 * np.average(lens))
        result['std_len'] = int(100 * np.std(lens))
        result['rel_std_len'] = int(100 * result['std_len'] / result['average_len'])

"""
This function computes calculates user command word statistics, in particular,
    word lengths.
"""
def calclangstats(seg, collected, result):
    result['nuniquewords'] = len(collected['n']) + len(collected['v'])
    result['nwords'] = sum([len(x[2]) for x in collected['n']]) +\
        sum([len(x[2]) for x in collected['v']])

    for e in ['nuniquewords', 'nwords']:
        key = 'rel' + e
        if result['nentries'] > 0:
            result[key] = int(100 * result[e] / float(result['nentries']))
        else:
            result[key] = -1

"""
This function handles the entire stats generation process by calling
    subordinate computation functions.
"""
def calcsegstats(seg, collected):
    result = {}

    overall1(seg, result)
    calclangstats(seg, collected, result)

    return result
