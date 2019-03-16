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
- provide credentials or an access token in a config file
  (see credentials.ini.in for a template, see below how to get client credentials or a token)
- add song links or track URI's to a text file (e.g. "tracks.txt"), one per line
- run the command
```
$ ./stl -l -i tracks.txt
```

- this will print a table with title/album/artist information to stdout and also
write a json files named "spotify-tracks\_\<datetime\>.json"

- to print a playlist just pass a playlist URL (can be obtained from the Spotify app: right click > Share > Copy Playlist Link)

```
$ ./stl -i https://open.spotify.com/user/myusername/playlist/3jZmUF8dQOIrMErfdxMfDP
```

## Credentials howto

The application requires either an access token or clientID and clientSecret.
The credentials must be provided within a config file (in ini format, one section named "spotify"):
```
[spotify]
ClientID = some_client_id
ClientSecret = some_client_secret
AccessToken = some_accesstoken
```
The default location for this file is "credentials.ini" in the project root, or the
`-c / --credentials` option can be used to pass the path to a file.

Either both of `ClientID`, `ClientSecret` or an `AccessToken` must be present.

### Howto get a clientID / -secret
- follow Spotify instructions to register an App:  
  https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app

### Howto get an OAuth accesstoken
- note: the token will expire after some time (currently 1 hour) and if there are
  no client credentials, the App won't be able to re-authenticate, so this works
  only for short-term usage
- go to web console https://developer.spotify.com/web-api/console/get-track/
- login to your Spotify account
- create token
- copy this token to the file "credentials.ini" (AuthToken = the_new_token)


## Troubleshooting

### UnicodeDecodeError
- UnicodeDecodeError while trying to write the output to a file:
```
$ ./stl -l -i tracks.txt >out.txt
...
UnicodeEncodeError: 'ascii' codec can't encode character u'\xfc' in position 46: ordinal not in range(128)
```
- set env variable `PYTHONIOENCODING`:
```
$ PYTHONIOENCODING=UTF-8 ./stl -l -i tracks.txt >out.txt
```