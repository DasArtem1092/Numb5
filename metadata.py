import os
import re
import glob
import click
from functools import reduce
import mutagen
from mutagen import mp3
from mutagen.id3 import ID3, TPE1, TPE2, TRCK, TIT2

# The main notable classes in mutagen are FileType, StreamInfo, Tags, Metadata and for error handling the MutagenError exception.



class MetadataDealer:

    _d = {'artist': TPE1,  # 4.2.1   TPE1    [#TPE1 Lead performer(s)/Soloist(s)]  ; taken from http://id3.org/id3v2.3.0
                             # in clementine temrs, it affects the 'Artist' tab but not the 'Album artist'
          'album_artist': TPE2}  # 4.2.1   TPE2    [#TPE2 Band/orchestra/accompaniment]
                                   # in clementine terms, it affects the 'Artist' tab but not the 'Album artist'

    # supported metadata to try and infer automatically
    _auto_data = [('track_number', TRCK),  # 4.2.1   TRCK    [#TRCK Track number/Position in set]
                  ('track_name', TIT2)]   # 4.2.1   TIT2    [#TIT2 Title/songname/content description]

    _all = dict(_d, **dict(_auto_data))

    reg = re.compile(r'(?:(\d{1,2})(?:[ \t]*[\-\.][ \t]*|[ \t]+)|^)?((?:\w+\b[ \t])*?\w+)(?:\.\w+)')  # use to parse track file names like "1. Loyal to the Pack.mp3"


    def set_album_metadata(self, album_directory, track_number=True, track_name=True, artist='', album_artist='', verbose=False):
        self._write_metadata(album_directory, verbose=verbose, track_number=track_number, track_name=track_name, artist=artist, album_artist=album_artist)

    def _write_metadata(self, album_directory, verbose=False, **kwargs):
        files = glob.glob('{}/*.mp3'.format(album_directory))
        print('FILES\n', list(map(os.path.basename, files)))
        for file in files:
            self.write_metadata(file, **dict(self._filter_auto_inferred(self._infer_track_number_n_name(file), **kwargs),
                                             **{'artist': kwargs.get('artist', ''),
                                                'album_artist': kwargs.get('album_artist', '')
                                                }))

    @classmethod
    def write_metadata(cls, file, **kwargs):
        assert all(map(lambda x: x[0] in cls._all.keys(), kwargs.items()))

        audio = ID3(file)
        # audio.add(TIT2(encoding=3, text=u"An example"))
        # metadata = mutagen.mp3.MP3(file)
        for k,v in kwargs.items():
            if bool(v):
                audio.add(cls._all[k](encoding=3, text=u'{}'.format(v)))
                # audio[cls._all[k]].text = [v]
                print("set '{}' with {}: {}={}".format(file, k, cls._all[k].__name__, v))
        audio.save()

    def _filter_auto_inferred(self, d, **kwargs):
        for k in self._auto_data:
            if not kwargs.get(k, False):
                try:
                    del d[k]
                except KeyError:
                    pass
        return d

    def _infer_track_number_n_name(self, file_name):
        
        return {k[0]: re.search(self.reg, file_name).group(i+1) for i,k in enumerate(self._auto_data)}

    # def _infer_track_number_n_name_test(self, file_name):
    #     r = {}
    #     print('FILE:', file_name)
    #     for i, k in enumerate(self._auto_data):
    #         c = re.search(self.reg, file_name)
    #         # print('KEY: {} gr {}'.format(k, i+1), c.group(i+1))
    #     return {k:re.search(self.reg, file_name).group(i+1) for i,k in enumerate(self._auto_data)}


@click.command()
@click.option('--album-dir', required=True, help="The directory where a music album resides. Currently only mp3 "
                                                          "files are supported as contents of the directory. Namely only "
                                                          "such files will be apprehended as tracks of the album.")
@click.option('--track_name/--no-track_name', default=True, show_default=True, help='Whether to extract the track names from the mp3 files and write them as metadata correspondingly')
@click.option('--track_number/--no-track_number', default=True, show_default=True, help='Whether to extract the track numbers from the mp3 files and write them as metadata correspondingly')
@click.option('--artist', '-a', help="If given, then value shall be used as the TPE1 tag: 'Lead performer(s)/Soloist(s)'.  In the music player 'clementine' it corresponds to the 'artist' column")
@click.option('--album_artist', help="If given, then value shall be used as the TPE2 tag: 'Band/orchestra/accompaniment'.  In the music player 'clementine' it corresponds to the 'Album artist' column")
def main(album_dir, track_name, track_number, artist, album_artist):
    md = MetadataDealer()
    md.set_album_metadata(album_dir, track_number=track_number, track_name=track_name, artist=artist, album_artist=album_artist, verbose=True)


def test():
    al = '/data/projects/music-album-creator/lttp'
    md = MetadataDealer()
    md.set_album_metadata(al, track_name=True, track_number=True, artist='gg', album_artist='navi', verbose=True)

if __name__ == '__main__':
    main()
    # test()

    #
    # from mutagen.mp3 import MP3
    #
    # f = MP3('/media/kostas/freeagent/m/Planet Of Zeus/Loyal To The Pack/01 - Loyal to the Pack.mp3')
    #
    # print(dir(f))