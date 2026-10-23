"""Importação de catálogo como dados; nenhum JavaScript do HTML é executado."""
import json
import queue
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import yt_dlp

from converter import convert


def load_catalog(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    match = re.search(r'\bconst\s+songs\s*=\s*', text)
    if not match:
        raise ValueError('Não encontrei a lista "const songs" neste HTML.')
    data, _ = json.JSONDecoder().raw_decode(text[match.end():])
    if not isinstance(data, list):
        raise ValueError('O catálogo precisa conter uma lista de músicas.')
    songs = []
    seen = set()
    for row in data:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in ('artist', 'title')):
            raise ValueError('Há uma música sem artista ou título válido.')
        song = {k: str(row.get(k, '')).strip() for k in ('artist', 'title', 'genre')}
        key = (song['artist'].casefold(), song['title'].casefold())
        if key not in seen:
            seen.add(key)
            songs.append(song)
    if not songs:
        raise ValueError('O catálogo está vazio.')
    return songs


def find_video(song):
    query = f"ytsearch1:{song['artist']} {song['title']} áudio oficial"
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'noplaylist': True, 'socket_timeout': 30}) as downloader:
        result = downloader.extract_info(query, download=False)
    entries = list(result.get('entries') or [])
    if not entries or not entries[0] or not entries[0].get('id'):
        raise ValueError('Nenhum resultado encontrado no YouTube.')
    return 'https://www.youtube.com/watch?v=' + entries[0]['id']


def run_batch(songs, folder, report, stop):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / 'relatorio-mp3.json'
    history = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    if not isinstance(history, dict):
        raise ValueError('O relatório existente tem formato inválido. Preserve-o e escolha outra pasta.')
    counts = {'salvos': 0, 'existentes': 0, 'falhas': 0}
    for index, song in enumerate(songs, 1):
        if stop.is_set():
            break
        key = json.dumps([song['artist'], song['title']], ensure_ascii=False)
        previous = history.get(key, {})
        label = f"{song['artist']} — {song['title']}"
        if previous.get('status') == 'salvo' and Path(previous.get('arquivo', '')).is_file():
            counts['existentes'] += 1
            report(index, 'Já salvo', label)
            continue
        record = dict(song)
        try:
            report(index, 'Pesquisando', label)
            url = find_video(song)
            record['url'] = url
            output = convert(url, folder, lambda msg: report(index, msg, label))
            record.update(status='salvo', arquivo=str(output))
            counts['salvos'] += 1
            report(index, 'Salvo', label)
        except Exception as error:
            record.update(status='erro', erro=str(error))
            counts['falhas'] += 1
            report(index, 'Erro: ' + str(error), label)
        history[key] = record
        temporary = manifest.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(manifest)
    return counts


def open_batch(parent):
    existing = getattr(parent, '_batch_window', None)
    if existing is not None and existing.winfo_exists():
        existing.lift()
        return
    window = tk.Toplevel(parent)
    parent._batch_window = window
    window.title('Baixar catálogo em lote')
    window.geometry('850x560')
    window.batch_running = False
    frame = ttk.Frame(window, padding=16)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Busca automática: o primeiro resultado pode ser cover ou outra versão.', wraplength=780).pack(anchor='w')
    ttk.Label(frame, text='Selecione as faixas desejadas (Ctrl/clique). Parar aguarda a faixa atual terminar.').pack(anchor='w', pady=5)
    songs = []
    events = queue.Queue()
    stop = threading.Event()
    busy = False
    folder = tk.StringVar(value=str(Path.home() / 'Downloads' / 'YouTube MP3'))
    status = tk.StringVar(value='Importe sua lista HTML para começar.')
    row = ttk.Frame(frame)
    row.pack(fill='x', pady=8)

    def load(path=None):
        nonlocal songs
        path = path or filedialog.askopenfilename(parent=window, filetypes=[('Lista HTML', '*.html')])
        if not path:
            return
        try:
            songs = load_catalog(path)
            tree.delete(*tree.get_children())
            for index, song in enumerate(songs):
                tree.insert('', 'end', iid=str(index), values=(song['artist'], song['title'], song['genre']))
            tree.selection_set(tree.get_children())
            status.set(f'{len(songs)} músicas importadas e selecionadas.')
        except Exception as error:
            messagebox.showerror('Falha ao importar', str(error), parent=window)

    load_button = ttk.Button(row, text='Importar HTML', command=load)
    load_button.pack(side='left')
    ttk.Button(row, text='Selecionar todas', command=lambda: tree.selection_set(tree.get_children())).pack(side='left', padx=8)
    tree_frame = ttk.Frame(frame)
    tree_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(tree_frame, columns=('artist', 'title', 'genre'), show='headings', selectmode='extended')
    for name, heading in [('artist', 'Artista'), ('title', 'Música'), ('genre', 'Estilo')]:
        tree.heading(name, text=heading)
        tree.column(name, width=230)
    scroll = ttk.Scrollbar(tree_frame, command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    tree.pack(fill='both', expand=True)
    destination = ttk.Frame(frame)
    destination.pack(fill='x', pady=10)
    ttk.Entry(destination, textvariable=folder).pack(side='left', fill='x', expand=True)

    def choose():
        selected = filedialog.askdirectory(parent=window)
        if selected:
            folder.set(selected)

    ttk.Button(destination, text='Pasta de destino', command=choose).pack(side='right')

    def worker(selected, target):
        try:
            result = run_batch(selected, target, lambda i, msg, label: events.put(('progress', f'{i}/{len(selected)} · {label}\n{msg}')), stop)
            events.put(('done', ' · '.join(f'{k}: {v}' for k, v in result.items())))
        except Exception as error:
            events.put(('done', 'Falha no lote: ' + str(error)))

    def start():
        nonlocal busy
        selected = [songs[int(i)] for i in tree.selection()]
        if not selected or not folder.get().strip():
            messagebox.showinfo('Seleção necessária', 'Selecione músicas e uma pasta de destino.', parent=window)
            return
        busy = True
        window.batch_running = True
        stop.clear()
        start_button.configure(state='disabled')
        load_button.configure(state='disabled')
        status.set('Iniciando…')
        threading.Thread(target=worker, args=(selected, folder.get()), daemon=True).start()

    controls = ttk.Frame(frame)
    controls.pack(fill='x')
    start_button = ttk.Button(controls, text='Baixar selecionadas', command=start)
    start_button.pack(side='left')
    ttk.Button(controls, text='Parar após esta faixa', command=stop.set).pack(side='left', padx=8)
    ttk.Label(frame, textvariable=status, wraplength=790).pack(anchor='w', pady=10)

    def poll():
        nonlocal busy
        for _ in range(100):
            try:
                kind, text = events.get_nowait()
            except queue.Empty:
                break
            status.set(text)
            if kind == 'done':
                busy = False
                window.batch_running = False
                start_button.configure(state='normal')
                load_button.configure(state='normal')
        window.after(150, poll)

    def close():
        if busy:
            stop.set()
            messagebox.showinfo('Aguarde', 'O lote vai parar ao terminar a faixa atual. Aguarde para fechar.', parent=window)
        else:
            window.destroy()

    window.protocol('WM_DELETE_WINDOW', close)
    window.after(150, poll)
    bundled = Path(__file__).with_name('LISTA_INTERATIVA.html')
    if bundled.exists():
        load(str(bundled))
