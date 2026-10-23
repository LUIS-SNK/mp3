import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.ffmpeg import FFmpegExtractAudioPP

from converter import convert, validate_url


class ConverterTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertEqual(validate_url(' https://youtu.be/abc '), 'https://youtu.be/abc')
        for url in ('file:///tmp/audio', 'https://youtube.com.evil.org/a', 'texto', 'https://example.com'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_download_and_postprocessing_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'Som [abc].mp3'
            output.write_bytes(b'fixture')
            with patch('converter.yt_dlp.YoutubeDL') as factory:
                client = factory.return_value.__enter__.return_value
                client.extract_info.return_value = {'id': 'abc'}
                client.prepare_filename.return_value = str(output.with_suffix('.webm'))
                self.assertEqual(convert('https://youtu.be/abc', tmp), output)
                client.extract_info.assert_called_once_with('https://youtu.be/abc', download=True)
                options = factory.call_args.args[0]
                self.assertTrue(options['noplaylist'])
                self.assertEqual(options['postprocessors'][0]['preferredcodec'], 'mp3')

    def test_missing_output_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp, patch('converter.yt_dlp.YoutubeDL') as factory:
            client = factory.return_value.__enter__.return_value
            client.prepare_filename.return_value = str(Path(tmp) / 'missing.webm')
            with self.assertRaises(RuntimeError):
                convert('https://youtu.be/abc', tmp)

    def test_real_ffmpeg_mp3_conversion(self):
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'sample.wav'
            subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', str(source)], check=True)
            with YoutubeDL({'ffmpeg_location': ffmpeg, 'quiet': True}) as downloader:
                processor = FFmpegExtractAudioPP(downloader, preferredcodec='mp3', preferredquality='192')
                _, info = processor.run({'filepath': str(source), 'ext': 'wav', 'vcodec': 'none', 'acodec': 'pcm_s16le'})
            output = Path(info['filepath'])
            self.assertEqual(output.suffix, '.mp3')
            self.assertGreater(output.stat().st_size, 1000)
            subprocess.run([ffmpeg, '-v', 'error', '-i', str(output), '-f', 'null', '-'], check=True)


if __name__ == '__main__':
    unittest.main()
