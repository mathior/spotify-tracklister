# spotify-tracklister
Show title/album/artist information for a list of spotify track URIs.

Problem: The spotify client (at least the the Linux desktop client) doesn't have
a function to copy title/album/artist information from tracks, one just can copy
song links (looking like https://open.spotify.com/track/7I1yaqAkqYo3P2BHApuGzE)
or track URI's (looking like spotify:track:7I1yaqAkqYo3P2BHApuGzE). I'd like to
get title/album/artist information.

Solution: Resolve track URI's using Spotifys API.

This tool reads a list of song links or track URI's from an input file and
prints a title/album/artist table.


## Requirements
- Python 2.7+, 3.0+
- requests


## Howto
- add song links or track URI's to a text file (e.g. "tracks.txt"), one per line
- add an auth token into a file named auth.token (see below how to get a token)
- run the command

$ python stl.py -l -i tracks.txt

- this will print a table with title/album/artist information to stdout and also
write a json files named "spotify-tracks\_\<datetime\>.json"

- to print a playlist just pass a playlist URL (can be obtained from the Spotify app: right click > Share > Copy Playlist Link)

$ python stl.py -i https://open.spotify.com/user/myusername/playlist/3jZmUF8dQOIrMErfdxMfDP



## Howto receive OAuth token
- go to web console https://developer.spotify.com/web-api/console/get-track/
- login to your spotify account
- create token (this also creates an cURL example call)
- copy this token to the file "auth.token"
- note: the token will expire after some time (1 hour)

