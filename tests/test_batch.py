import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from batch import find_video, load_catalog, run_batch


class BatchTests(unittest.TestCase):
    def test_import_real_catalog(self):
        songs = load_catalog(Path(__file__).resolve().parents[1] / 'LISTA_INTERATIVA.html')
        self.assertGreater(len(songs), 100)
        self.assertEqual(songs[0]['artist'], 'Tião Carreiro & Pardinho')

    def test_import_data_without_executing_javascript_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'list.html'
            song = {'artist': 'Artista', 'title': 'Música'}
            path.write_text('const songs=' + json.dumps([song, song]) + ';throw new Error();', encoding='utf-8')
            self.assertEqual(len(load_catalog(path)), 1)
            path.write_text('const songs=[{}];', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_catalog(path)

    def test_search(self):
        with patch('batch.yt_dlp.YoutubeDL') as factory:
            client = factory.return_value.__enter__.return_value
            client.extract_info.return_value = {'entries': [{'id': 'abc'}]}
            self.assertEqual(find_video({'artist': 'A', 'title': 'B'}), 'https://www.youtube.com/watch?v=abc')
            client.extract_info.return_value = {'entries': []}
            with self.assertRaises(ValueError):
                find_video({'artist': 'A', 'title': 'B'})

    def test_continue_after_error_and_resume(self):
        songs = [{'artist': 'A', 'title': 'Um'}, {'artist': 'B', 'title': 'Dois'}]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'Um.mp3'
            output.write_bytes(b'audio')
            with patch('batch.find_video', return_value='https://youtu.be/abc'), patch('batch.convert', side_effect=[output, RuntimeError('indisponível')]):
                counts = run_batch(songs, tmp, lambda *args: None, threading.Event())
            self.assertEqual(counts, {'salvos': 1, 'existentes': 0, 'falhas': 1})
            history = json.loads((Path(tmp) / 'relatorio-mp3.json').read_text(encoding='utf-8'))
            self.assertEqual(len(history), 2)
            with patch('batch.find_video', return_value='https://youtu.be/def'), patch('batch.convert', return_value=output) as convert:
                counts = run_batch(songs, tmp, lambda *args: None, threading.Event())
                self.assertEqual(convert.call_count, 1)
            self.assertEqual(counts['existentes'], 1)
            self.assertEqual(counts['salvos'], 1)

    def test_stop_before_next_song(self):
        with tempfile.TemporaryDirectory() as tmp, patch('batch.find_video') as search:
            stop = threading.Event()
            stop.set()
            result = run_batch([{'artist': 'A', 'title': 'B'}], tmp, lambda *args: None, stop)
            search.assert_not_called()
            self.assertEqual(sum(result.values()), 0)
