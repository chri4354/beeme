"""
The functions here compare an action command to the most popular chat commands
    by various comparison algorithms. 
They all have the same three arguments:
    - command: the action command, a string
    - incoming: the sorted tally of noun / verb / 2-combo popularities, derived
        from the chat messages.
    - time: the time stamp of the action command

"""

#*_maxindexs: max indices for the various tests below. See exact interpretation
#    under the test functions.
loose_full_match_maxindex = 3
bag_of_words_maxindex = 3
indicator_test_maxindex = 5
moment_test_maxindex = 5
decay_test_maxindex = 5
decay_cutoff_secs = 50
decay_dampener = 5 * 1000
"""
Full test: an exact string match between the action command and the most
    popular (=frequent) 2-combination. If the most popular hit is not unique,
    i.e. two or more 2-combinations have the same number of occurrences,
    result is undefined -- the basis of comparison is always the 2-combination
    that is the first on the popularity-sorted list.
The test returns 1 if and only if the test passes, 0 otherwise.
"""
def full_test(command, incoming, time):
    #nothing matches an empty list or an empty command
    if len(command) == 0 or (len(incoming['t']) == 0):
        return 0

    #a full match is ok...
    if incoming['t'][0][1] == command:
        print "FULL MATCH", command, incoming['t'][0]
        return 1

    #...but nothing else is
    return 0

"""
Loose full test: very much akin to the full test, but here the basis of 
    comparison is the first _n_ 2-combos, rather than the first only.
    Result may be undefined in case the popularity counts are not unique.
The test returns 1 if and only if the test passes, 0 otherwise.
"""
def loose_full_test(command, incoming, time):    
    #nothing matches an empty list or an empty command
    if len(command) == 0 or (len(incoming['t']) == 0):
        return 0

    #a full match on any of the most popular items is ok...
    for e in incoming['t'][:loose_full_match_maxindex]:
        if e[1] == command:
            return 1
    #...but nothing else is
    return 0

"""
Bag of words test: in contrast to the tests above, this test considers both
    chat 2-combos and action commands to be unsorted sets of words, rather than
    sorted strings. The test generates the word set for the action command,
    as well as the most popular 2-combos from chat commands, and for each 
    2-combination, it computes the fraction of words of the action command 
    that are in it.
    The return value is the maximum over all chat 2-combination considered.
This function returns a fractional value on [0,1], signifying match strength.
"""
def bagofwords1(command, incoming, time):    
    combow = set(command.split())
    #nothing matches an empty list or an empty command
    if len(incoming['t']) == 0 or len(combow) == 0:
        return 0

    reslst = []
    #for each chat command, calculate the set and measure it against the
    #action command set.
    for e in incoming['t'][:bag_of_words_maxindex]:
        bow2 = set(e[1].split())
        cnt = 0
        for e2 in bow2:
            if e2 in combow:
                cnt += 1
        reslst.append(cnt)                

    #return the max        
    return max(reslst) / float(len(combow))

"""
Indicator test: a discretized version of the bag of words test. Both the
    action command and the chat 2-combo is converted into a bag of words,
    but rather than returning the highest fractional match, this function
    returns 1 if and only if one of the 2-combinations contain at least
    half of the action command's words, and 0 otherwise.
"""
def indicator_test(command, incoming, time):    
    combow = set(command.split())
    #nothing matches an empty list or an empty command
    if len(incoming['t']) == 0 or len(combow) == 0:
        return 0

    reslst = []
    for e in incoming['t'][:indicator_test_maxindex]:
        bow2 = set(e[1].split())
        if len(combow.intersection(bow2)) >= 0.5 * len(combow):
            print "INDI MATCH!: {0}".format(e)
            return 1

    return 0

"""
Moment test: the moment test is very similar to the indicator test in terms
    of the matching, but it resorts the 2-combo candidate list based on
        weight and "moment".
    Each 2-combination is assigned the root mean square value of the time stamps
        it appeared at. This will produce a bias towards end of the segment.
    Matching is similar to the indicator, in that it will produce a match on
        a candidate if the candidate contains at least half of the words from
        the action command. Unlike the indicator, this function will also
        produce a match if the action command contains at least 80% of the
        candidate's terms. This is a simple heuristic addition, meant to
        deal with long action commands and short 2-combos (e.g. action=
        "make earl tea", chat="tea"). Note that the "2-combo" here is a 
        single word, as the input was a single word..
Returns 1 if and only if there was a match, 0 otherwise.
"""
def moment_test(command, incoming, time):
    combow = set(command.split())
    #nothing matches an empty list or an empty command
    if len(incoming['t']) == 0 or len(combow) == 0:
        return 0
    moments = []
    #produce the root mean square value for each 2-combo on the entire 
    #2-combo set.
    for e in incoming['t']:
        assert(e[0] > 0)
        m1 = 0
        wt = 0
        for i2 in range(e[0]):
            m1 += (1*i2+1)*e[2][i2]**2
            wt += 1.0
        m1 = (m1/wt)**0.5

        moments.append((m1, e[1]))

    #inverse sort by RMS value        
    std = list(reversed(sorted(moments)))
#    print "MOMENT:::", std[:5]

    combow = set(command.split())

    reslst = []
    #now, essentially an indicator test, with the difference outlined above
    for e in std[:moment_test_maxindex]:
        bow2 = set(e[1].split())
        li = len(combow.intersection(bow2))
        if li >= 0.5 * len(combow) or li >= 0.8 * len(bow2):
            print "MOMENT MATCH!: {0}".format(e)
            return 1


    return 0


"""
The decay test is a more sophisticated form of the moment test that goes 
    beyond the segmentation mentality, and support online computation mode.
    Sorting here (given an action command time stamp) is done as follows:
        1. all 2-combos whose time is beyond a certain distance from the
            action time stamp are ignored.
        2. For all remaining time stamps, the weight associated with that
            time stamp is proportional to 1/sqrt(d+x), where x is the
            time difference from the action time, and d is a dampening 
            constant, to avoid a bias towards instances very close to the
            action time stamp.
    Once sorted as above, matching is identical to the way seen in the moment
        test.
"""
def decay_test(command, incoming, time):
    cutoff = decay_cutoff_secs * 1000

    combow = set(command.split())
    #nothing matches an empty list or an empty command
    if len(incoming['t']) == 0 or len(combow) == 0:
        return 0

    bydecay = []
    #calculate weights by decay
    for e0 in incoming['t']:
        assert(e0[0] > 0)
        e = (e0[0], e0[1], 
            [x for x in e0[2] if x <= time and time - x < cutoff])

        m1 = 0
        wt = 0
        for xx in e[2]:
            wt += 1000.0 / ((time + decay_dampener - xx) ** 0.5)

        bydecay.append((wt, e[1]))
    std = list(reversed(sorted(bydecay)))
    print "DECAY:::", std[:1]

    combow = set(command.split())

    reslst = []
    for e in std[:decay_test_maxindex]:
        bow2 = set(e[1].split())
        li = len(combow.intersection(bow2))
        if li >= 0.5 * len(combow) or li >= 0.8 * len(bow2):
            print "DECAY MATCH!: {0}".format(e)
            return 1


    return 0


