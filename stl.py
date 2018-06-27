#!/usr/bin/env python

import sys
import json
import time
import requests
import re
import argparse

"""Extracts some information from the JSON result of an Spotify API tracks
request.
"""

# create a token in the console:
# https://developer.spotify.com/web-api/console/get-several-tracks/


class TracksProcessor(object):

    def __init__(self, token):
        self.__token = token

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
            if '?' in tid:
                # remove query parameters from urls
                tid = tid[:tid.find('?')]
            trackids.append(tid)
        return trackids


class PlaylistProcessor(object):

    def __init__(self, token):
        self.__token = token

    def extract(self, jsondata):

        d = {
            'name': jsondata['name'],
            'description': jsondata['description'],
            'owner': jsondata['owner']['id'],
            'uri': jsondata['uri'],
            'total': jsondata['tracks']['total'],
        }

        tracks = []
        for e in jsondata['tracks']['items']:
            t = e['track']
            td = {
                'title': t['name'],
                'artist': [a['name'] for a in t['artists']],
                'album': t['album']['name'],
                'tracknum': t['track_number'],
                'discnum': t['disc_number'],
                'duration': t['duration_ms'],
                'explicit': t['explicit'],
                'uri': t['uri'],
            }
            tracks.append(td)

        d['tracks'] = tracks

        return d

    def loadplaylistdata(self, playlist):

        # possible playlist values:
        # https://api.spotify.com/v1/users/joshschwaa/playlists/5kp8ZfRfhRzqJTpl5lpQeW
        # https://open.spotify.com/user/joshschwaa/playlist/5kp8ZfRfhRzqJTpl5lpQeW
        # spotify:user:joshschwaa:playlist:5kp8ZfRfhRzqJTpl5lpQeW

        urlpat = 'https://api.spotify.com/v1/users/{}/playlists/{}'
        url = None
        if playlist.startswith('https://api.spotify.com/v1/'):
            url = playlist
        else:
            if playlist.startswith('https://open.spotify.com/user/'):
                openurl = re.compile('.*user/(?P<user>.*?)/playlist/(?P<plid>.*)')
                m = openurl.match(playlist)
            elif playlist.startswith('spotify:'):
                uri = re.compile('spotify:user:(?P<user>.*?):playlist:(?P<plid>.*)')
                m = uri.match(playlist)
            else:
                raise Exception('{} is not a playlist URL/URL'.format(playlist))
            if m:
                url = urlpat.format(
                    m.groupdict()['user'], m.groupdict()['plid'])

        if not url:
            raise Exception('no API URL')

        pljson = self._load(url)
        nexturl = pljson['tracks']['next']
        # nexturl is null when the playlist is not paged
        while nexturl:
            nextjson = self._load(nexturl)
            items = nextjson['items']  # with offset there is no 'tracks' field
            pljson['tracks']['items'].extend(items)
            nexturl = nextjson['next']
        return pljson

    def _load(self, url):
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.__token)}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print('Error while loading playlist: {} {}'.format(res.status_code, res.reason))
            print(res.text)
            raise Exception('Error while loading playlist')
        return res.json()


class TablePrinter(object):

    def __init__(self, tracktablefields, multifields=None):
        # tracktablefields defines what and in which order should be printed
        # multifields defines fields with more than one possible value
        self.__tracktablefields = tracktablefields
        self.__multifields = multifields if multifields else []
        self.__tracksfieldname = 'tracks'  # tracks key in a playlist

    def printplaylist(self, data, playlistfields=('name', 'description', 'owner', 'uri', 'total')):
        for f in playlistfields:
            print('# {}: {}'.format(f, data[f]))
        self.printtracktable(data[self.__tracksfieldname])

    def printtracktable(self, data):
        out = []
        maxlen = [0] * len(self.__tracktablefields)
        for d in data:
            l = []
            for i, f in enumerate(self.__tracktablefields):
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
                  for i, f in enumerate(self.__tracktablefields)]
        print(' | '.join(header))
        hline = ['-' * maxlen[i] for i, _ in enumerate(self.__tracktablefields)]
        print('---'.join(hline))
        for outline in out:
            l = [f.ljust(maxlen[i], ' ') for i, f in enumerate(outline)]
            print(' | '.join(l))


def savejson(jsondata, filename, sort_keys=False):
    with open(filename, 'w') as fout:
        json.dump(jsondata, fout, indent=4, sort_keys=sort_keys)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extracts some information from the JSON result of an Spotify API tracks request.')
    parser.add_argument(
        '-t', '--token', dest='token', help='OAuth token (obtained from Spotify)')
    parser.add_argument('-i', '--input', dest='input', help='Input URI/URL/file', required=True)
    parser.add_argument(
        '-l', '--tracklistmode', dest='tracklistmode', action='store_true',
        help='Input is a file listing Spotify track URIs or links instead of a playlist  URI or URL')
    parser.add_argument(
        '-R', '--from-raw', dest='fromraw', action='store_true',
        help='Input is a saved raw API response that should be print as table')
    parser.add_argument(
        '-r', '--saveraw', dest='saveraw', action='store_true', help='(optional flag) save raw API response')
    parser.add_argument('-n', '--name', dest='name', help='(optional) filename for output files')

    args = parser.parse_args()

    if not args.token:
        try:
            with open('auth.token') as f:
                token = f.readline().strip()
        except IOError as e:
            print('missing token argument and "auth.token" file')
            parser.print_help()
            sys.exit(0)
    else:
        token = args.token

    inputval = args.input
    fromraw = args.fromraw

    ts = time.strftime('%Y-%m-%dT%H%M%S%Z', time.localtime())
    outname = ('{}_{}'.format(args.name, ts)
               if args.name
               else 'spotify-list_{}'.format(ts))

    printer = TablePrinter(['title', 'album', 'artist'], multifields=['artist'])

    if args.tracklistmode:
        tp = TracksProcessor(token)

        if fromraw:
            rawapiresponse = json.loads(open(inputval).read())
            extracted = tp.extract(rawapiresponse)
        else:
            tids = tp.loadtrackids(inputval)
            response = tp.loadtracksdata(tids)
            if not response:
                sys.exit(1)
            if args.saveraw:
                savejson(response, outname + '_raw.json')
            extracted = tp.extract(response)
            savejson(extracted, outname + '.json', True)
        printer.printtracktable(extracted)
    else:
        pp = PlaylistProcessor(token)
        if fromraw:
            rawapiresponse = json.loads(open(inputval).read())
            try:
                extracted = pp.extract(rawapiresponse)
            except KeyError:
                print('{} is not a raw playlist (try -l for tracklist mode)'.format(inputval))
                sys.exit(1)
        else:
            try:
                response = pp.loadplaylistdata(inputval)
            except Exception as e:
                print(e.message)
                sys.exit(1)
            if not response:
                sys.exit(1)
            if args.saveraw:
                savejson(response, outname + '_raw.json')
            extracted = pp.extract(response)
            savejson(extracted, outname + '.json', True)
        printer.printplaylist(extracted)
