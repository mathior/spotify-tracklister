#!/usr/bin/env python

import sys
import json
import time
from subprocess import check_output, CalledProcessError

"""Extracts some information from the JSON result of an Spotify API tracks
request.
"""

# create a token in the console https://developer.spotify.com/web-api/console/get-several-tracks/

# defines what and in which order should be printed
PRINTFIELDS = [
    'title',
    'album',
    'artist',
]


def extract(jsondata):
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


def save(jsondata, filename):
    with open(filename, 'w') as fout:
        json.dump(jsondata, fout, indent=4, sort_keys=True)


def printtable(data):
    out = []
    maxlen = [0] * len(PRINTFIELDS)
    for d in data:
        l = []
        for i, f in enumerate(PRINTFIELDS):
            val = d[f]
            if f == 'artist':
                s = (', '.join(val))
                l.append(s)
            else:
                l.append(val)
            vallen = len(l[i])
            maxlen[i] = vallen if vallen > maxlen[i] else maxlen[i]
        out.append(l)
    header = [f.capitalize().ljust(maxlen[i], ' ')
              for i, f in enumerate(PRINTFIELDS)]
    print(' | '.join(header))
    hline = ['-' * maxlen[i] for i, _ in enumerate(PRINTFIELDS)]
    print('---'.join(hline))
    for outline in out:
        l = [f.ljust(maxlen[i], ' ') for i, f in enumerate(outline)]
        print(' | '.join(l))


def loadtracksdata(trackidlist, token):
    ids = ','.join(trackidlist)
    url = 'https://api.spotify.com/v1/tracks?ids={}'.format(ids)
    authheader = 'Authorization: Bearer {}'.format(token)
    try:
        output = check_output(['curl', '-X', 'GET', url, '-H', 'Accept: application/json', '-H', authheader])
    except CalledProcessError as e:
        print(e)
        sys.exit(1)
    response = json.loads(output)
    if 'error' in response:
        print(output)
        sys.exit(1)
    else:
        return(response)


def loadtrackids(filename):
    with open(filename) as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    trackids = []
    for l in lines:
        if l.startswith('spotify:track:'):
            tid = l.replace('spotify:track:', '')
            trackids.append(tid)
        elif l.startswith('https://open.spotify.com/track/'):
            tid = l.replace('https://open.spotify.com/track/', '')
            trackids.append(tid)
        else:
            continue
    return trackids


if __name__ == '__main__':
    tracklistfile = sys.argv[1]
    
    try:
        with open('auth.token') as f:
            token = f.readline().strip()
    except IOError as e:
        token = sys.argv[2]
    
    ts = time.strftime('%Y-%m-%dT%H:%M:%S%Z', time.localtime())
    
    tids = loadtrackids(tracklistfile)
    
    response = loadtracksdata(tids, token)
    if not response:
        sys.exit(1)
        
    with open('spotify-tracks_{}_raw.json'.format(ts), 'w') as fout:
        json.dump(response, fout, indent=4)
    
    e = extract(response)
    
    printtable(e)
    
    save(e, 'spotify-tracks_{}.json'.format(ts))

    
