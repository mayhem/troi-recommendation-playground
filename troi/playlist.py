import subprocess
import ujson

from troi.operations import is_homogeneous


def _serialize_recordings_to_listen_format(entities):

    if not is_homogeneous(entities, "recording"):
        raise TypeError("entity list not homogeneous")


    listens = []
    for e in entities:
        artist_mbids = [ str(mbid) for mbid in e.mb_artist.get('artist_mbids', []) ]
        listens.append({
            'listened_at' : 0,
            'track_metadata' : {
                'artist_name' : e.mb_artist.get('artist_credit_name', ''),
                'track_name' : e.name,
                'release_name' : e.mb_release.get('release_name', ''),
                'additional_info' : {
                    'recording_mbid' : str(e.id),
                    'artist_mbids' : artist_mbids
                }
            }
        })

    return ujson.dumps(listens, indent=4, sort_keys=True)


def launch_playlist(playlist):

    json_playlist = _serialize_recordings_to_listen_format(playlist)
    subprocess.run(['./openpost.py', '-s', '-k', '--key', 'listens', 'https://listenbrainz.org/player'], input=json_playlist, encoding="utf-8")