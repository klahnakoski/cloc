# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals
from __future__ import division
import sys
import math
from .cube import Cube
from ..queries.index import value2key
from ..struct import StructList, Struct
from ..structs.wraps import listwrap, wrap
from ..env.logs import Log
from ..collections.multiset import Multiset


def groupby(data, keys=None, size=None, min_size=None, max_size=None, contiguous=False):
    """
        return list of (keys, values) pairs where
            group by the set of keys
            values IS LIST OF ALL data that has those keys
        contiguous - MAINTAIN THE ORDER OF THE DATA, STARTING THE NEW GROUP WHEN THE SELECTOR CHANGES
    """

    if size != None or min_size != None or max_size != None:
        if size != None:
            max_size = size
        return groupby_min_max_size(data, min_size=min_size, max_size=max_size)

    if isinstance(data, Cube):
        return data.groupby(keys)

    keys = listwrap(keys)
    def get_keys(d):
        output = Struct()
        for k in keys:
            output[k] = d[k]
        return output

    if contiguous:
        try:
            if not data:
                return wrap([])

            agg = StructList()
            acc = StructList()
            curr_key = value2key(keys, data[0])
            for d in data:
                key = value2key(keys, d)
                if key != curr_key:
                    agg.append((get_keys(acc[0]), acc))
                    curr_key = key
                    acc = [d]
                else:
                    acc.append(d)
            agg.append((get_keys(acc[0]), acc))
            return wrap(agg)
        except Exception, e:
            Log.error("Problem grouping contiguous values", e)

    try:
        agg = {}
        for d in data:
            key = value2key(keys, d)
            pair = agg.get(key, None)
            if pair is None:
                pair = (get_keys(d), StructList())
                agg[key] = pair
            pair[1].append(d)

        return agg.values()
    except Exception, e:
        Log.error("Problem grouping", e)


def groupby_size(data, size):
    if hasattr(data, "next"):
        iterator = data
    elif hasattr(data, "__iter__"):
        iterator = data.__iter__()
    else:
        Log.error("do not know how to handle this type")

    done = StructList()
    def more():
        output = StructList()
        for i in range(size):
            try:
                output.append(iterator.next())
            except StopIteration:
                done.append(True)
                break
        return output

    # THIS IS LAZY
    i = 0
    while True:
        output = more()
        yield (i, output)
        if len(done) > 0:
            break
        i += 1


def groupby_Multiset(data, min_size, max_size):
    # GROUP multiset BASED ON POPULATION OF EACH KEY, TRYING TO STAY IN min/max LIMITS
    if min_size == None:
        min_size = 0

    total = 0
    i = 0
    g = list()
    for k, c in data.items():
        if total < min_size or total + c < max_size:
            total += c
            g.append(k)
        elif total < max_size:
            yield (i, g)
            i += 1
            total = c
            g = [k]

        if total >= max_size:
            Log.error("({{min}}, {{max}}) range is too strict given step of {{increment}}", {
                "min": min_size, "max": max_size, "increment": c
            })

    if g:
        yield (i, g)


def groupby_min_max_size(data, min_size=0, max_size=None, ):
    if max_size == None:
        max_size = sys.maxint

    if isinstance(data, (bytearray, basestring, list)):
        def _iter():
            num = int(math.ceil(len(data)/max_size))
            for i in range(0, num):
                output = (i, data[i * max_size:i * max_size + max_size:])
                yield output

        return _iter()

    elif hasattr(data, "__iter__"):
        def _iter():
            g = 0
            out = StructList()
            for i, d in enumerate(data):
                out.append(d)
                if (i + 1) % max_size == 0:
                    yield g, out
                    g += 1
                    out = StructList()
            if out:
                yield g, out

        return _iter()
    elif not isinstance(data, Multiset):
        return groupby_size(data, max_size)
    else:
        return groupby_Multiset(data, min_size, max_size)

