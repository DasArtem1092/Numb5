import os
import re
import time


class StringParser:
    __instance = None
    timestamp_objects = {}
    sep = r'(?:[\t ]+|[\t ]*[\-\.]+[\t ]*)'

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def duration_data_to_timestamp_data(cls, duration_data):
        """Call this to transform data concerning tracks' starting timestamps to tracks' time duration. In both cases the format is hh:mm:ss"""
        return [list(_) for _ in cls._gen_timestamp_data(duration_data)]

    @staticmethod
    def _gen_timestamp_data(duration_data):
        """
        :param list of lists duration_data: each inner list has as 1st element a track name and as 2nd the track duration in hh:mm:s format
        :return: list of lists with timestamps instead of durations ready to feed for segmentation
        :rtype: list
        """
        i = 1
        p = Timestamp('0:00')
        yield duration_data[0][0], str(p)
        while i < len(duration_data):
            yield duration_data[i][0], str(p + Timestamp(duration_data[i-1][1]))
            p += Timestamp(duration_data[i-1][1])
            i += 1

    @classmethod
    def parse_hhmmss_string(cls, tracks):
        """Call this method to transform a '\n' separabale string of album tracks to a list of lists. Inner lists contains [track_name, hhmmss_timestamp].\n
        :param str tracks:
        :return:
        """
        return [_ for _ in cls._parse_string(tracks)]

    @classmethod
    def _parse_string(cls, tracks):
        """
        :param str tracks: a '\n' separable string of lines coresponding to the tracks information
        :return:
        """
        # regex = re.compile('(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w\'\(\) ]*[\w)])' + cls.sep + '((?:\d?\d:)*\d?\d)$')
        for i, line in enumerate(_.strip() for _ in tracks.split('\n')):
            if line == '':
                continue
            try:
                yield cls._parse_track_line(line)
            except AttributeError:
                raise WrongTimestampFormat("Couldn't parse line {}: '{}'. Please use a format as 'trackname - 3:45'".format(i + 1, line))

    @classmethod
    def _parse_track_line(cls, track_line):
        """Parses a string line such as '01. Doteru 3:45'"""
        regex = re.compile(r"""^(?:\d{1,2}(?:[\ \t]*[\.\-,][\ \t]*|[\t\ ]+))?  # potential track number (eg 01) included is ignored
                                    ([\w\'\(\) ’]*[\w)])                       # track name
                                    (?:[\t ]+|[\t ]*[\-\.]+[\t ]*)            # separator between name and time
                                    ((?:\d?\d:)*\d?\d)$                       # time in hh:mm:ss format""", re.X)
        # regex = re.compile('^(?:\d{1,2}([\ \t]*[\.\-,][ \t]*|[\t ]+))?([\w\'\(\) ]*[\w)])' + cls.sep + '((?:\d?\d:)*\d?\d)$')
        # regex = re.compile(
        #     '^(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w\'\(\) ]*[\w)])' + cls.sep + '((?:\d?\d:)*\d?\d)$')
        return list(regex.search(track_line.strip()).groups())

    @classmethod
    def get_instance(cls):
        return StringParser()

    @classmethod
    def parse_tracks_hhmmss(cls, tracks_row_strings):
        """
        Call this method to transform a
        Returns parsed tracks: track_title and timestamp in hh:mm:ss format given the multiline string. Ignores potentially
        found track numbers in the start of each line  Returs a list of lists. Each inner list holds the captured groups in the parenthesis'\n
        :param str tracks_row_strings:
        :return: a list of lists with each inner list corresponding to each input string row and having 2 elements: the track name and the timestamp
        :rtype: list
        """
        regex   = re.compile(r'(?:\d{1,2}[ \t]*[\.\-,][ \t]*|[\t ]+)?([\w ]*\w)' + cls.sep + r'((?:\d?\d:)*\d?\d)')
        # regex = re.compile('(?:\d{1,2}(?:[ \t]*[\.\-,][ \t]*|[\t ])+)?([\w ]*\w)' + cls.sep + '((?:\d?\d:)*\d\d)')

        return [list(_) for _ in regex.findall(tracks_row_strings)]

    @classmethod
    def hhmmss_durations_to_timestamps(cls, hhmmss_list):
        return [_ for _ in cls._generate_timestamps(hhmmss_list)]

    @classmethod
    def _generate_timestamps(cls, hhmmss_list):
        i, p = 1, '0:00'
        yield p
        for el in hhmmss_list[:-1]:
            _ = cls.add(p, el)
            yield _
            p = _

    @classmethod
    def convert_to_timestamps(cls, tracks_row_strings):
        """Accepts tracks durations in hh:mm:ss format; one per row"""
        lines = cls.parse_tracks_hhmmss(tracks_row_strings)  # list of lists
        i = 1
        timestamps = ['0:00']
        while i < len(lines):
            timestamps.append(cls.add(timestamps[i-1], lines[i-1][-1]))
            i += 1
        return timestamps

    @classmethod
    def add(cls, timestamp1: str, duration: str) -> object:
        """
        :param str timestamp1: hh:mm:ss
        :param str duration: hh:mm:ss
        :return: hh:mm:ss
        :rtype: str
        """
        return cls.time_format(cls.to_seconds(timestamp1) + cls.to_seconds(duration))

    @staticmethod
    def to_seconds(timestamp):
        """Call this method to transform a hh:mm:ss formatted string timestamp to its equivalent duration in seconds as an integer"""
        return sum([60**i * int(x) for i, x in enumerate(reversed(timestamp.split(':')))])

    @staticmethod
    def time_format(seconds):
        """Call this method to transform an integer representing time duration in seconds to its equivalent hh:mm:ss formatted string representeation"""
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    @staticmethod
    def parse_album_info(video_title):
        """Parses a video title string into 'artist', 'album' and 'year' fields.\n
        Can parse patters:
         - Artist Album Year\n
         - Album Year\n
         - Artist Album\n
         - Album\n
        :param video_title:
        :return: the exracted values as a dictionary having maximally keys: {'artist', 'album', 'year'}
        :rtype: dict
        """
        sep1 = r'[\t ]*[\-\.][\t ]*'
        sep2 = r'[\t \-\.]+'
        year = r'\(?(\d{4})\)?'
        art = r'([\w ]*\w)'
        alb = r'([\w ]*\w)'
        _reg = lambda x: re.compile(str('{}' * len(x)).format(*x))

        reg1 = _reg([art, sep1, alb, sep2, year])
        m1 = reg1.search(video_title)
        if m1:
            return {'artist': m1.group(1), 'album': m1.group(2), 'year': m1.group(3)}

        m1 = _reg([alb, sep2, year]).search(video_title)
        if m1:
            return {'album': m1.group(1), 'year': m1.group(2)}

        reg2 = _reg([art, sep1, alb])
        m2 = reg2.search(video_title)
        if m2:
            return {'artist': m2.group(1), 'album': m2.group(2)}

        reg3 = _reg([alb])
        m3 = reg3.search(video_title)
        if m3:
            return {'album': m3.group(1)}
        return {}

    @classmethod
    def convert_tracks_data(cls, data, album_file, target_directory=''):
        """
        Converts input Nx2 list of lists to Nx3 list of lists. The exception being the last list that has 2 elements\n
        :param list of lists data: each inner list should contain track title (no need for number and without extension)
        and starting time stamp in hh:mm:ss format
        :param str album_file: the path to the audio file of the entire album to potentially segment
        :param str target_directory: path to desired directory path to store the potentially created album
        :return: each iner list contains track title and timestamp in seconds
        :rtype: list of lists
        """
        return [list(_) for _ in cls._generate_data(data, album_file, target_directory)]

    @classmethod
    def _generate_data(cls, data, album_file, target_directory):
        """
        Given a data list, with each element representing an album's track (as an inner 2-element list with 1st element the 'track_name' and 2nd a timetamp in hh:mm:ss format (the track starts it's playback at that timestamp in relation with the total album playtime), the path to the alum file at hand and the desired output directory or potentially storing the track files,
        generates 3-length tuples with the track_file_path, starting timestamp and ending timestamp. Purpose is for the yielded tripplets to be digested for audio segmentation. The exception being the last tuple yielded that has 2 elements; it naturally misses the ending timestamp.\n
        :param list data:
        :param str album_file:
        :param str target_directory:
        :returns: 3-element tuples with track_name, starting_timestamp, ending_timestamp
        :rtype: tuple
        """
        cls.__album_file = album_file
        cls.__target_directory = target_directory
        cls.__track_index_generator = iter((lambda x: str(x) if 9 < x else '0' + str(x))(_) for _ in range(1, len(data) + 1))
        for i in range(len(data)-1):
            if Timestamp(data[i + 1][1]) <= Timestamp(data[i][1]):
                raise TrackTimestampsSequenceError(
                    "Track '{} - {}' starting timestamp '{}' should be 'bigger' than track's '{} - {}'; '{}'".format(
                        i + 2, data[i + 1][0], data[i + 1][1],
                        i + 1, data[i][0], data[i][1]))
            yield (
                cls.__track_file(data[i][0]),
                str(int(Timestamp(data[i][1]))),
                str(int(Timestamp(data[i + 1][1])))
            )
        yield (
            cls.__track_file(data[-1][0]),
            str(int(Timestamp(data[-1][1]))),
        )

    @classmethod
    def __track_file(cls, track_name):
        return os.path.join(cls.__target_directory, '{} - {}{}'.format(
            next(cls.__track_index_generator),
            track_name,
            (lambda x: '.' + x.split('.')[-1] if len(x.split('.')) > 1 else '')(cls.__album_file)))


class Timestamp:
    instances = {}
    def __new__(cls, *args, **kwargs):
        hhmmss = args[0]
        if hhmmss in cls.instances:
            return cls.instances[hhmmss]
        match = re.fullmatch(r'((\d?\d):){0,2}(\d?\d)', hhmmss)
        if not match:
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))
        values = [int(_) for _ in hhmmss.split(':')]
        if not all([0 <= _ <= 60 for _ in values]):
            raise WrongTimestampFormat("Timestamp given: '{}'. Please use the 'hh:mm:ss' format.".format(hhmmss))
        x = super().__new__(cls)
        x._s = sum([60 ** i * int(x) for i, x in enumerate(reversed(values))])
        x._b = hhmmss
        cls.instances[hhmmss] = x
        return x

    def __init__(self, hhmmss):
        pass

    @staticmethod
    def from_duration(seconds):
        return Timestamp(time.strftime('%H:%M:%S', time.gmtime(seconds)))
    def __repr__(self):
        return self._b
    def __str__(self):
        return self._b
    def __eq__(self, other):
        return str(self) == str(other)
    def __int__(self):
        return self._s
    def __lt__(self, other):
        return int(self) < int(other)
    def __le__(self, other):
        return int(self) <= int(other)
    def __gt__(self, other):
        return int(other) < int(self)
    def __ge__(self, other):
        return int(other) <= int(self)
    def __add__(self, other):
        return Timestamp.from_duration(int(self) + int(other))
    def __sub__(self, other):
        return Timestamp.from_duration(int(self) - int(other))


class WrongTimestampFormat(Exception): pass
class TrackTimestampsSequenceError(Exception): pass

