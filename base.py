import codecs
import csv
import sys

import matplotlib.pyplot as plt

"""
The Event class handles basic information related to 'events'. These evets are 
either a chat message or an action performed by the actor.
"""
class Event:
    eventctr = 0
    def __init__(self, time, typ, actor, command, literal_command):
        if type(time) == tuple:
            self.timestamp = time
        elif type(time) == str:
            self.timestamp = clock2tuple(time)
        else:
            assert(0)
        
        self.actor = actor
        self.type = typ.lower()
        self.ctr = Event.eventctr
        self.command = command
        self.original_command = literal_command
        Event.eventctr += +1

    def __str__(self):
        return "{0}: {1}, {2}, type {3}, '{4}'".format(self.ctr,
            self.actor, self.timestamp, self.type, self.command)

"""
The Segment class represents an 'action segment', i.e. a time interval that
culminates in the actor confirming a command. Thus, these segments contain
the following events:
    - an arbitrary number of chat message events
    - a single action command.
"""
class Segment:
    """
    Contructor
    """
    def __init__(self, start_time, end_time, command, entries):
        self.start_time = start_time
        self.end_time = end_time
        self.command = command
        self.entries = entries
        self.mlclass = 0

    """
    String representation of the object
    """
    def __str__(self):
        s =  ["SEGMENT {0}-{1}".format(self.start_time, self.end_time)]
        s.append("    Command: " + self.command.__str__())
        for e in self.entries:
            s.append("\t" + e.__str__())
        return '\n'.join(s)

    """
    The filter trims the segment by removing all chat messages outside the
    specified time interval. The segment's time coverage interval is trimmed
    along the way, so subsequent calls to this function with a filter value
    that is a proper subset of [0, 1] will keep cutting the segment.
    Therefore, in typical use this function should not be called more than
    once on a segment.
    """
    def filter(self, fracs = [0, 1]):
        if len(self.entries) < 3:
            return

        t1 = tuple2int(self.entries[0].timestamp)
        t2 = tuple2int(self.entries[-1].timestamp)
        diff = t2 - t1

        newvals = (int(fracs[0] * diff + t1), int(fracs[1] * diff + t1))

        newents = []
        for e in self.entries:
            t = tuple2int(e.timestamp)
            if t < newvals[0] or t > newvals[1]:
                continue
            newents.append(e)
        if len(newents) > 0:
            self.start_time = newents[0].timestamp
            self.end_time = newents[-1].timestamp
        else:
            self.start_time = -1
            self.end_time = -1
        self.entries = newents

##################
#Utility functions
##################


"""
Convert time integer value to a tuple of (hour, minute, second, millisecond).
"""
def clock2tuple(stamp):
    xl = stamp.split(':')
    assert(len(xl) == 3)
    xl2 = xl[2].split(',')
    assert(len(xl2) == 2)

    return (int(xl[0]), int(xl[1]), int(xl2[0]), int(xl2[1]))

"""
Convert time tuple value (hour, minute, second, millisecond) to integer.
"""
def tuple2int(stamp):
    return 3600000 * stamp[0] + 60000 * stamp[1] + 1000 * stamp[2] + stamp[3]

def int2tuple(t):
    hour = t // 3600000
    carry = t % 3600000
    minute = carry // 60000
    carry = carry % 60000
    second = carry // 1000
    carry = carry % 1000

    return (hour, minute, second, carry)

"""
Read chat and action source files and return them as a time-sorted list of
events.
"""
def read_sources(srt, chat):
    res_unso = []
    with codecs.open(srt, 'rt') as srtf:
        srt_reader = csv.reader(srtf, delimiter = ',')
        for e in srt_reader:
            assert(len(e) == 4)
            if e[2] != '':
                ee = Event(e[1], 'r', '_ACTOR_', e[2].lower(), e[3])
                res_unso.append(ee)

    with codecs.open(chat, 'rt') as chf:
        ch_reader = csv.reader(chf, delimiter = ',')
        for e in ch_reader:
            assert(len(e) == 4)
            ee = Event(e[0], '_', e[1], e[2].lower(), e[3])
            res_unso.append(ee)
           

    #now sort
    sorter = [(x.timestamp, x) for x in res_unso]
    return [x[1] for x in sorted(sorter)]

"""
Compares two time tuples, returns -1 if the first one is smaller, +1 if the
second, and 0 if they are equal.
"""
def timerel(a, b):
    for i in range(4):
        if a[i] < b[i]:
            return -1
        if b[i] < a[i]:
            return 1
    return 0

"""
Return the difference between two time tuples in milliseconds.
"""
def difftm(tm, diffms, setto0=False):
#    assert(diffms > 0)
    tval = 3600000 * tm[0] + 60000 * tm[1] + 1000 * tm[2] + tm[3]
    if setto0:
        if tval < diffms:
            return (0, 0, 0, 0)
#    assert(tval > diffms)
    newt = tval - diffms
    return int2tuple(newt)

#    hour = newt // 3600000
#    carry = newt % 3600000
#    minute = carry // 60000
#    carry = carry % 60000
#    second = carry // 1000
#    carry = carry % 1000

#    return (hour, minute, second, carry)

"""
Converts a time-sorted representation of the input events into segments.
"""
def build_segments(timeline, opdelay):
    result = []
    actl = [i for i in range(len(timeline)) if timeline[i].actor == '_ACTOR_']
    start = 0
    for e in actl:
        nt = difftm(timeline[e].timestamp, opdelay)
        start_time = nt
        end_time = nt
        entries = []
        for i in range(start, len(timeline)):
            if timeline[i].actor == '_ACTOR_':
                continue
            if timerel(timeline[i].timestamp, nt) == -1:
                entries.append(timeline[i])
                if i == start:
                    start_time = timeline[i].timestamp
                end_time = timeline[i].timestamp
            else:
                break
        start = i

        sg = Segment(start_time, end_time, timeline[e], entries)
        result.append(sg)

    return result

"""
Creates all word pairs of a string of words retaining the order.
"""
def twocombos(l):
    if len(l) == 0:
        return []
    elif len(l) == 1:
        return [[l[0][:-2]]]

    result = []
    for i in range(len(l) - 1):
        for j in range(i + 1, len(l)):
            result.append([l[i][:-2], l[j][:-2]])
    return result

def nvkeys(words):
    assert(len(words) > 0)

    initcands = twocombos(words)

    result = [(' '.join(x), 1.0) for x in initcands]

    if len(initcands[0]) == 1:
        key = initcands[0][0]
        return result

    return result

"""
Calculates match scores based on a variety of tests. Tests are specified in
the variable sctests.
"""
def calc_scores(command, sctests, statted, mem, orig_command):
    for e in sctests:
        if e[0] not in mem:
            mem[e[0]] = (0, 0)
        sc = e[1](command, statted, tuple2int(orig_command.timestamp))
        mem[e[0]] = (mem[e[0]][0] + sc, mem[e[0]][1] + 1)

"""
Collects statistics for a segment.
"""
def stat_segment(segment):
    mem = {'n': {}, 'v': {}, 't': {}}

    for e in segment.entries:
        assert(e.actor != '_ACTOR_')
        wlist = e.command.split(' ')
        tkeys = nvkeys(wlist)

        for e2 in tkeys:
            if e2[0] not in mem['t']:
                mem['t'][e2[0]] = []
            tt0 = e.timestamp
            tt = 3600000 * tt0[0] + 60000 * tt0[1] + 1000 * tt0[2] + tt0[3]
            mem['t'][e2[0]].append(tt)

        for e2 in wlist:
            xl = e2.split('+')
            key = xl[1]
            k2 = xl[0]
            if k2 not in mem[key]:
                mem[key][k2] = []
            tt0 = e.timestamp
            tt = 3600000 * tt0[0] + 60000 * tt0[1] + 1000 * tt0[2] + tt0[3]
            mem[key][k2].append(tt)



    for e2 in ['n', 'v', 't']:
        sorter = list(reversed(sorted([(len(v), k, v) for 
            k, v in mem[e2].items()])))
        mem[e2] = sorter
    return mem

if __name__ == "__main__":
    pass
