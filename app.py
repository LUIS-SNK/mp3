import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import convert, validate_url
from batch import open_batch


def main():
    root = tk.Tk()
    root.title('YouTube → MP3')
    root.geometry('640x380')
    root.minsize(540, 380)
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='YouTube → MP3', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
    ttk.Label(frame, text='Cole um link e salve o áudio no seu computador.').pack(anchor='w', pady=(4, 16))
    url = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=url)
    entry.pack(fill='x')
    entry.focus()
    folder = tk.StringVar(value=str(Path.home() / 'Downloads' / 'YouTube MP3'))
    row = ttk.Frame(frame)
    row.pack(fill='x', pady=12)
    ttk.Entry(row, textvariable=folder).pack(side='left', fill='x', expand=True)
    choose = ttk.Button(row, text='Escolher pasta', command=lambda: select_folder())
    choose.pack(side='right', padx=(8, 0))
    status = tk.StringVar(value='Pronto para baixar.')
    events = queue.Queue()
    busy = False

    def select_folder():
        selected = filedialog.askdirectory(parent=root)
        if selected:
            folder.set(selected)

    def worker(link, destination):
        try:
            output = convert(link, destination, lambda msg: events.put(('progress', msg)))
            events.put(('done', str(output)))
        except Exception as error:
            events.put(('error', str(error)))

    def start():
        nonlocal busy
        try:
            link = validate_url(url.get())
            if not folder.get().strip():
                raise ValueError('Escolha uma pasta para salvar o MP3.')
        except ValueError as error:
            messagebox.showerror('Verifique os campos', str(error), parent=root)
            return
        busy = True
        button.configure(state='disabled')
        status.set('Conectando ao YouTube…')
        threading.Thread(target=worker, args=(link, folder.get()), daemon=True).start()

    def poll():
        nonlocal busy
        for _ in range(100):
            try:
                kind, text = events.get_nowait()
            except queue.Empty:
                break
            if kind == 'progress':
                status.set(text)
            else:
                busy = False
                button.configure(state='normal')
                status.set('MP3 salvo!' if kind == 'done' else 'Não foi possível concluir.')
                if kind == 'done':
                    messagebox.showinfo('Concluído', f'Arquivo salvo em:\n{text}', parent=root)
                else:
                    messagebox.showerror('Falha no download', text + '\n\nVídeos privados, restritos ou bloqueados podem não estar disponíveis.', parent=root)
        root.after(100, poll)

    def close():
        if any(getattr(child, 'batch_running', False) for child in root.winfo_children()):
            messagebox.showinfo('Lote em andamento', 'Pare o lote e aguarde a faixa atual terminar antes de sair.', parent=root)
            return
        if not busy or messagebox.askyesno('Sair', 'Há um download em andamento. Deseja interromper e sair?', parent=root):
            root.destroy()

    button = ttk.Button(frame, text='Baixar MP3', command=start)
    button.pack(anchor='w', pady=(4, 12))
    ttk.Button(frame, text='Baixar lista de músicas em lote…', command=lambda: open_batch(root)).pack(anchor='w', pady=(0, 12))
    ttk.Label(frame, textvariable=status, wraplength=560).pack(anchor='w')
    ttk.Label(frame, text='Use apenas conteúdos que você tem autorização para baixar.', foreground='#666666').pack(anchor='w', side='bottom')
    root.protocol('WM_DELETE_WINDOW', close)
    root.after(100, poll)
    root.mainloop()


if __name__ == '__main__':
    main()
