from pathlib import Path
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp


def validate_url(value):
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in (
        'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be'
    ):
        raise ValueError('Cole um link válido do YouTube.')
    return value


def convert(url, folder, report=lambda message: None):
    url = validate_url(url)
    folder = Path(folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)

    def progress(data):
        if data['status'] == 'downloading':
            total = data.get('total_bytes') or data.get('total_bytes_estimate')
            if total:
                report(f"Baixando: {data.get('downloaded_bytes', 0) / total:.0%}")
            else:
                report('Baixando áudio…')
        elif data['status'] == 'finished':
            report('Convertendo para MP3…')

    options = {
        'format': 'bestaudio/best',
        'outtmpl': str(folder / '%(title).150B [%(id)s].%(ext)s'),
        'windowsfilenames': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 3,
        'quiet': True,
        'js_runtimes': {'node': {}},
        'no_warnings': True,
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'progress_hooks': [progress],
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        output = Path(downloader.prepare_filename(info)).with_suffix('.mp3')
    if not output.is_file():
        raise RuntimeError('A conversão terminou sem gerar o MP3 esperado.')
    return output
