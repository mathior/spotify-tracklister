#!/usr/bin/env python

import sys
import json
import time
import requests
import re

"""Extracts some information from the JSON result of an Spotify API tracks
request.
"""

# create a token in the console:
# https://developer.spotify.com/web-api/console/get-several-tracks/


class TracksProcessor(object):

    def __init__(self, token, name=None):
        self.__token = token
        self.__name = name

    def extract(self, jsondata):
        tracks = jsondata['tracks']
        extracted = []
        for t in tracks:
            d = {
                'title': t['name'],
                'artist': [a['name'] for a in t['artists']],
                'album': t['album']['name'],
                'tracknum': t['track_number'],
                'discnum': t['disc_number'],
                'duration': t['duration_ms'],
                'explicit': t['explicit'],
                'uri': t['uri'],
            }
            extracted.append(d)
        return extracted

    def loadtracksdata(self, trackidlist):
        ids = ','.join(trackidlist)
        url = 'https://api.spotify.com/v1/tracks?ids={}'.format(ids)
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.__token)}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            print('Error while loading tracks: {} {}'.format(res.status_code, res.reason))
            print(res.text)

    def loadtrackids(self, filename):
        with open(filename) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        trackids = []
        ifpat = re.compile('<iframe src="https://open.spotify.com/embed/track/(.*?)".*</iframe>')
        for l in lines:
            if l.startswith('spotify:track:'):
                tid = l.replace('spotify:track:', '')
            elif l.startswith('https://open.spotify.com/track/'):
                tid = l.replace('https://open.spotify.com/track/', '')
            elif l.startswith('https://open.spotify.com/embed/track/'):
                tid = l.replace('https://open.spotify.com/embed/track/', '')
            elif l.startswith('<iframe src="https://open.spotify.com/embed/track/'):
                m = ifpat.match(l)
                if m:
                    tid = m.group(1)
            else:
                continue
            trackids.append(tid)
        return trackids

    def processfile(self, tracklistfile, saveraw=False):
        tids = self.loadtrackids(tracklistfile)

        response = self.loadtracksdata(tids)
        if not response:
            sys.exit(1)
        if saveraw:
            ts = time.strftime('%Y-%m-%dT%H:%M:%S%Z', time.localtime())
            fn = ('{}_{}_raw.json'.format(self.__name, ts)
                  if self.__name
                  else 'spotify-tracks_{}_raw.json'.format(ts))
            savejson(response, fn)

        return self.extract(response)


class TablePrinter(object):

    def __init__(self, printfields, multifields=None):
        # printfields defines what and in which order should be printed
        # printfields defines fields with more than one possible value
        self.__printfields = printfields
        self.__multifields = multifields if multifields else []

    def printtable(self, data):
        out = []
        maxlen = [0] * len(self.__printfields)
        for d in data:
            l = []
            for i, f in enumerate(self.__printfields):
                val = d[f]
                if f in self.__multifields:
                    s = (', '.join(val))
                    l.append(s)
                else:
                    l.append(val)
                vallen = len(l[i])
                maxlen[i] = vallen if vallen > maxlen[i] else maxlen[i]
            out.append(l)
        header = [f.capitalize().ljust(maxlen[i], ' ')
                  for i, f in enumerate(self.__printfields)]
        print(' | '.join(header))
        hline = ['-' * maxlen[i] for i, _ in enumerate(self.__printfields)]
        print('---'.join(hline))
        for outline in out:
            l = [f.ljust(maxlen[i], ' ') for i, f in enumerate(outline)]
            print(' | '.join(l))


def savejson(jsondata, filename, sort_keys=False):
    with open(filename, 'w') as fout:
        json.dump(jsondata, fout, indent=4, sort_keys=sort_keys)


if __name__ == '__main__':
    tracklistfile = sys.argv[1]
    
    try:
        with open('auth.token') as f:
            token = f.readline().strip()
    except IOError as e:
        token = sys.argv[2]
    
    ts = time.strftime('%Y-%m-%dT%H:%M:%S%Z', time.localtime())

    tp = TracksProcessor(token)
    e = tp.processfile(tracklistfile, saveraw=True)

    printer = TablePrinter(['title', 'album', 'artist'], multifields=['artist'])
    printer.printtable(e)

    savejson(e, 'spotify-tracks_{}.json'.format(ts), True)
