# YouTube → MP3

Aplicativo simples para Windows: cole um link do YouTube, escolha a pasta e clique em **Baixar MP3**. Roda localmente, sem servidor ou conta própria. A conexão com a internet é necessária para baixar os vídeos.

## Como usar no Windows

1. Instale o **Python 3.11 ou mais recente** de https://www.python.org/downloads/windows/ com o Python Launcher e o suporte a Tcl/Tk (incluídos na instalação padrão).
2. Instale também o **Node.js LTS 22 ou mais recente** de https://nodejs.org/ (necessário para os desafios JavaScript do YouTube). Baixe ou clone este repositório e extraia os arquivos para uma pasta.
3. Dê dois cliques em **Iniciar.bat**. Na primeira execução, ele cria um ambiente Python e instala as dependências. As execuções seguintes verificam essas dependências.
4. Cole o link, escolha uma pasta e clique em **Baixar MP3**. Aguarde a confirmação antes de fechar o programa.

O FFmpeg é fornecido pela dependência `imageio-ffmpeg`; não é preciso instalá-lo separadamente. Os arquivos são salvos em `Downloads\YouTube MP3` por padrão, em MP3 a 192 kbps. Essa taxa não aumenta a qualidade do áudio original. Links de playlists baixam apenas o vídeo selecionado. Arquivos com mesmo título e ID podem ser reutilizados ou substituídos pelo yt-dlp; escolha outra pasta para manter cópias separadas.

Use apenas conteúdos próprios ou que você tenha autorização para baixar. Vídeos privados, com restrições de idade, região ou bloqueios do YouTube podem falhar. O aplicativo não solicita cookies ou credenciais e não contorna essas restrições.

## Baixar a lista em lote

Clique em **Baixar lista de músicas em lote…**. A lista `LISTA_INTERATIVA.html` incluída no pacote será carregada automaticamente. Você também pode importar outro HTML no mesmo formato (`const songs` com uma lista JSON de artista e título). O HTML é lido como dados, sem executar JavaScript.

Todas as músicas começam selecionadas. Use Ctrl/clique para escolher faixas ou **Selecionar todas**, escolha a pasta e clique em **Baixar selecionadas**. O programa busca artista e título no YouTube e usa o **primeiro resultado**, que pode ser um cover, versão ao vivo ou gravação incorreta. Para escolher uma versão exata, use o download por link na tela principal.

O lote processa uma faixa por vez e continua quando uma falha. **Parar após esta faixa** preserva o trabalho concluído. O arquivo `relatorio-mp3.json`, na pasta escolhida, registra cada resultado, link encontrado, caminho do MP3 e eventuais erros. Ao executar novamente na mesma pasta, faixas já salvas e ainda presentes são puladas; falhas são tentadas outra vez. Não apague o relatório se quiser retomar. As marcações de “já tenho” feitas no navegador não estão no HTML e não são importadas.

Use uma única janela de lote por pasta de destino para evitar gravações concorrentes no relatório. Nenhuma música é baixada antes de você iniciar o lote. Use somente conteúdos que tenha autorização para baixar.

## Desenvolvimento e testes

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O YouTube muda com frequência. Se um vídeo público deixar de funcionar, verifique a versão mais recente do yt-dlp e atualize a versão fixada em `requirements.txt` após testar.
