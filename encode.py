#!/usr/bin/env python
import argparse
import logging
import os
import re
import subprocess
import shutil


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Encoder(object):
    """
    Class for encoding media files.

    :param str input_dir: The input directory
    :param str destination_dir: The destination directory
    :param str working_dir: The working directory
    :param bool delete_source_file: If the source file should be deleted
    """

    def __init__(self, input_dir, destination_dir, working_dir='/tmp',
                 delete_source_file=False,
                 handbrake_cli='/usr/bin/HandBrakeCLI'):
        self.input_dir = input_dir
        self.destination_dir = destination_dir
        self.working_dir = working_dir
        self.delete_source_file = delete_source_file
        self.handbrake_cli = handbrake_cli
        self.valid_extensions = ['.mkv', '.mp4', '.m4v', '.avi', '.wmv', '.ts']

    def media_files(self):
        """
        Finds media files in the given directory.

        This method determines if a file is a media file based on the data in
        :py:attr:`valid_extensions`.

        :return: The media files
        :rtype: list
        """
        media_files = []
        for root, dirs, files in os.walk(self.input_dir):
            logger.debug('Searching %s for media files', root)
            for filename in files:
                if os.path.splitext(filename)[1] in self.valid_extensions:
                    media_files.append(
                        os.path.abspath(os.path.join(root, filename)))
        logger.debug('Found media files %s', media_files)
        return media_files

    def encode_media_files(self):
        """
        Encodes the media files that are not sample files.
        """
        for media_file in self.media_files():
            if not self.sample_file(media_file):
                handbrake = Handbrake(media_file, exe=self.handbrake_cli)
                output_file = handbrake.encode()
                self.move_file(output_file)
                if self.delete_source_file:
                    self.delete_file(media_file)

    @classmethod
    def sample_file(cls, filename):
        """
        Determines if a file is a sample file.

        This method is useful determining if a file is a sample file instead
        of a file that needs to be encoded.

        :param str filename: The filename
        :return: True if file is a sample file, otherwise False
        :rtype: bool
        """
        match = re.search(r'sample', filename, re.IGNORECASE)
        if match:
            logger.debug('%s is a sample file', filename)
            return True
        return False

    @classmethod
    def delete_file(cls, filename):
        """
        Deletes the given filename.

        :param str filename: The filename to delete
        :return: True if the delete was successful, otherwise False
        :rtype: bool
        """
        if os.path.exists(filename):
            try:
                os.remove(filename)
                return True
            except OSError:
                logger.exception('Error attempting to delete %s', filename)
                return False
        else:
            logger.warning('Unable to delete (file does not exist) %s',
                           filename)
            return False

    def move_file(self, filename):
        """
        Moves the given filename to the given destination directory.

        :param str filename: The filename to move
        :return: True if the move was successful, otherwise False
        :rtype: bool
        """
        if not os.path.exists(self.destination_dir):
            try:
                logger.debug('Creating %s', self.destination_dir)
                os.makedirs(self.destination_dir)
            except OSError:
                logger.exception('Error attempting to create %s',
                                 self.destination_dir)
                return False
        if os.path.exists(filename):
            destination_file = os.path.join(self.destination_dir,
                                            os.path.basename(filename))
            try:
                shutil.move(filename, destination_file)
                return True
            except OSError:
                logger.exception('Error attempting to move %s to %s',
                                 filename, destination_file)
        else:
            logger.error('Unable to move (files does not exist) %s', filename)
        return False


class Handbrake(object):
    """
    Class for interacting with Handbrake.

    :param str media_file: The media file
    :param str working_dir: The working directory
    :param str exe: The Handbrake CLI executable
    """

    def __init__(self, media_file, exe, working_dir='/tmp'):
        self.media_file = media_file
        self.working_dir = working_dir
        self.executable = exe

    def encode(self, preset='AppleTV 3'):
        """
        Encodes the media file using the given preset.

        :param str preset: The preset
        :return: The output file generated
        :rtype: str
        """
        logger.info('Starting encode of %s', self.media_file)
        output_file = os.path.join(
            self.working_dir,
            os.path.basename(self.media_file).replace(
                os.path.splitext(self.media_file)[1], '.m4v')
        )
        cmd = ' '.join([self.executable,
                        '--input="{}"'.format(self.media_file),
                        '--output="{}"'.format(output_file),
                        '--preset="{}"'.format(preset)])
        subprocess.call(cmd, shell=True)
        logger.info('Completed encode of %s', self.media_file)
        return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir',
                        help='the directory containing media files')
    parser.add_argument('destination_dir',
                        help='the directory to output the encoded files')
    parser.add_argument('-w', '--working_dir', default='/tmp',
                        help='the working directory to use while encoding')
    parser.add_argument('-hb', '--handbrake', default='/usr/bin/HandBrakeCLI',
                        help='the path to the HandBrake CLI executable')
    parser.add_argument('-d', '--delete_source', action='store_true',
                        help='delete the source media files after encoding')
    args = parser.parse_args()
    encoder = Encoder(args.input_dir, args.destination_dir,
                      delete_source_file=args.delete_source,
                      handbrake_cli=args.handbrake)
    encoder.encode_media_files()
