# AFTER — Assistive Framework for Therapeutic Experiential Reality

Este repositório contém o **AFTER**, um sistema local (offline) para **captura de vídeo** e **análise de movimento** com visualizações (heatmap/timeline/métricas), onde o **filtro Sobel** é executado em **hardware (FPGA)** e integrado a uma aplicação **Electron**.

- **Plataforma FPGA alvo**: **Intel/Altera DE10‑Lite**, **50 MHz**
- **Versão “final” do projeto Quartus (arquivada)**: `pipeline-sobel-fpga/quartus/sobel_2_g.qar`
- **Manual do usuário (operação clínica)**: `after-app/docs/manual_usuario.md`

---

## Visão geral (o que roda e por quê)

O sistema é composto por três blocos principais:

- **Aplicação Electron (UI)**: grava sessões de webcam e permite visualizar progresso/resultados.
- **Worker Python (pipeline/analytics)**: observa as sessões gravadas, processa o vídeo quadro-a-quadro, fala com a FPGA via serial e gera `heatmap` + métricas.
- **FPGA (HDL/Quartus)**: recebe um frame (160×120 bytes), aplica Sobel e devolve o frame filtrado (160×120 bytes) pela UART.

### Diagrama de arquitetura (alto nível)

```text
[after-app (Electron + React)]
  - captura webcam -> sessions/<id>/original.webm
  - cria job.json (pending)
  - lista sessões e reproduz resultados (file://)

            (filesystem: after-app/sessions/)
                     |
                     v
[after-app/python/worker.py (Python)]
  - encontra jobs pending
  - decodifica original.webm -> frames (OpenCV)
  - PC -> FPGA (UART 115200 8N1) -> PC
  - gera heatmap.webm + analytics.json
  - atualiza job.json (processing/done/error + progresso)

                     |
                     v
[DE10-Lite @ 50MHz (Quartus/Verilog)]
  - RX UART: stream 160x120 bytes (grayscale 8-bit)
  - kernel_sobel: Sobel streaming
  - TX UART: stream 160x120 bytes (sobel 8-bit)
```

---

## Fluxos principais (end-to-end)

### 1) Gravação de sessão (UI → disco)

1. A UI grava webcam via `MediaRecorder`.
2. Ao finalizar, a UI cria `after-app/sessions/<timestamp>/` e escreve:
   - `original.webm`
   - `job.json` com `status: "pending"`

Código de referência:
- `after-app/src/views/RecordView.jsx` (gravação/criação de sessão)
- `after-app/preload.js` (API file-based exposta para o renderer)

### 2) Processamento (Worker → FPGA → disco)

1. O `worker.py` faz polling na pasta `after-app/sessions/`.
2. Para cada sessão com `job.json.status == "pending"`:
   - abre `original.webm`
   - converte cada quadro para **160×120 grayscale**
   - envia para a FPGA via UART
   - recebe o frame Sobel (160×120)
   - acumula deltas e gera `heatmap.webm` + `analytics.json`
   - atualiza `job.json` com progresso e status final (`done`/`error`)

Código de referência:
- `after-app/python/worker.py`

### 3) Reprodução/Análise (UI ← disco)
<img width="1558" height="717" alt="image" src="https://github.com/user-attachments/assets/4dfa6bc0-637f-4978-bb22-e88f11cae395" />

1. A tela “Sessões” lê periodicamente `job.json` de cada sessão e mostra status/progresso.
2. A tela “Reproduzir” abre:
   - `original.webm`
   - `heatmap.webm` (quando existir)
   - `analytics.json` (métricas e timeline)


<img width="1558" height="717" alt="image" src="https://github.com/user-attachments/assets/dd0af2ca-d26f-4b3a-aff5-cdf9b9823701" />

Código de referência:
- `after-app/src/views/SessionsView.jsx`
- `after-app/src/views/PlaybackView.jsx`

---

## Contratos entre componentes (o que “cola” tudo)

### A) Contrato de arquivos por sessão (filesystem API)

Cada sessão é uma pasta em `after-app/sessions/<session_id>/`:

- **`original.webm`**: vídeo bruto capturado pela UI.
- **`job.json`**: estado e progresso do processamento.
  - `status`: `pending | processing | done | error`
  - `total_frames`, `processed_frames`
  - `error` (quando houver)
- **`heatmap.webm`**: vídeo processado (colormap “inferno”).
- **`analytics.json`**: métricas (intensidade, periodicidade, regularidade, zonas) + timeline.

Observação importante: o renderer (React) não chama um backend HTTP; ele apenas **lê/escreve arquivos** via `preload.js` (Electron `contextBridge`).

### B) Contrato Serial (PC ↔ FPGA)

- **Link**: UART
- **Configuração**: **115200**, **8N1**
- **Formato de frame (input/output)**:
  - **Um frame = 160 × 120 = 19200 bytes**
  - **8-bit grayscale**
  - **Sem header**: o frame é delimitado pela contagem de bytes (controle interno no FPGA).

### C) Contrato de resolução

- O worker envia para a FPGA em **160×120**.
- O worker recebe **160×120** e faz upscale para a resolução do vídeo original para gerar `heatmap.webm`.

---

## Mapa da codebase (onde está o quê)

### Produto (fluxo principal com Electron + FPGA)

- **UI / Electron**
  - `after-app/main.js`: processo principal do Electron
  - `after-app/preload.js`: API para acessar `after-app/sessions/` (list/read/write)
  - `after-app/src/`: UI React
    - `src/views/RecordView.jsx`: captura e gravação
    - `src/views/SessionsView.jsx`: lista sessões e status
    - `src/views/PlaybackView.jsx`: player + painel de analytics

- **Worker / processamento**
  - `after-app/python/worker.py`: loop principal do pipeline + analytics
  - `after-app/python/requirements.txt`: dependências (OpenCV, numpy, pyserial, Pillow)

- **FPGA / HDL**
  - `pipeline-sobel-fpga/quartus/verilog/sobel.v`: top-level (amarra RX/TX + UC/FD)
  - `pipeline-sobel-fpga/quartus/verilog/sobel_uc.v`: FSM de alto nível (recebe → processa → transmite)
  - `pipeline-sobel-fpga/quartus/verilog/sobel_processing_unit_fd.v`: buffers + kernel + mux de fim de imagem
  - `pipeline-sobel-fpga/quartus/verilog/kernel_sobel.v`: Sobel streaming (janela 3×3 + line buffers + flush)
  - `pipeline-sobel-fpga/quartus/verilog/framebuffer_sequencial.v`: framebuffer sequencial (endereçamento por contadores)
  - UART:
    - `pipeline-sobel-fpga/quartus/verilog/rx_serial_8N1.v`
    - `pipeline-sobel-fpga/quartus/verilog/tx_serial_8N1.v`

### POCs / Ferramentas (fora do fluxo principal)

Estas pastas existem para validar a ideia/efeito final antes do hardware:

- `video-feed-stub/`: gera um “sobel fake” sintético e publica num device `v4l2loopback` (Linux).
- `pipeline-sobel-software-only/`: Sobel em software e publicação como câmera virtual.
- `delta-visualization/`: consumidor que gera heatmap por delta temporal a partir de um feed (útil para inspeção/validação visual).
- `pipeline-sobel-fpga/src/`: protótipos de transceiver/captura (precede o worker do AFTER).

---

## Detalhes low-level por subprojeto (mapa interno)

Esta seção descreve “o que cada bloco faz internamente” em um nível prático (entrypoints, I/O, contratos e arquivos centrais), para acelerar navegação do código.

### `after-app/` — Electron + React (UI)

- **Responsabilidade**: capturar sessão (webcam) e apresentar playback + métricas; persistir tudo em disco.
- **Entrypoints**
  - **Processo principal**: `after-app/main.js` (cria `BrowserWindow`, carrega `dist/index.html`).
  - **Bridge (renderer ↔ filesystem)**: `after-app/preload.js` (expõe `window.api.*` via `contextBridge`).
  - **UI React**: `after-app/src/main.jsx` → `after-app/src/App.jsx`.
- **I/O (filesystem)**
  - **Escrita**: `preload.js:createSession()` cria `sessions/<id>/original.webm` + `job.json`.
  - **Leitura**: `listSessions()`, `readJob()`, `readAnalytics()`, `fileExists()`, `getSessionFile()`.
- **Playback**
  - `PlaybackView.jsx` usa `file://<path>` para apontar `<video src="...">` para arquivos locais.
- **Observações de design**
  - A UI **não fala com o worker por HTTP/IPC custom**; o acoplamento é via **arquivos** na pasta `sessions/`.

### `after-app/python/` — `worker.py` (pipeline + analytics)

- **Responsabilidade**: observar `after-app/sessions/`, processar `original.webm` e produzir `heatmap.webm` + `analytics.json` + atualizar `job.json`.
- **Entrypoint**
  - `after-app/python/worker.py` (função `main()`): loop de polling a cada `POLL_INTERVAL` segundos.
- **Descoberta de jobs**
  - `find_pending_jobs(SESSIONS_DIR)` procura sessões com `job.json.status == "pending"`.
  - `update_job(session_path, **updates)` mantém `job.json` como “fonte da verdade” do progresso.
- **Pipeline de frames (núcleo do sistema)**
  - `get_video_info()` lida com WebM com metadados ruins (FPS/frame_count “suspeitos”).
  - `frame_to_fpga_format(frame)`:
    - converte BGR → grayscale
    - resize para **160×120**
    - serializa como bytes (19200 bytes por frame)
  - Loop: **send frame → wait response → upsample → acumula heatmap → escreve frame no `heatmap.webm`**.
- **Analytics**
  - `compute_periodicity()` (FFT na timeline amostrada)
  - `compute_rhythm_regularity()` (picos acima de percentil → regularidade)
  - `compute_hot_zones()` (grade 3×3 e percentuais)
- **Dependências**
  - `after-app/python/requirements.txt`: `opencv-python`, `numpy`, `pyserial`, `Pillow`, `tqdm`.
- **Modos de falha relevantes**
  - Serial indisponível/ocupada, timeout de frame, `VideoWriter` não abre, `original.webm` ausente → `job.json.status="error"`.

### `pipeline-sobel-fpga/quartus/` — Projeto Quartus + HDL (DE10‑Lite @ 50MHz)

- **Projeto “final” arquivado**: `pipeline-sobel-fpga/quartus/sobel_2_g.qar`
- **Top-level e blocos**
  - `verilog/sobel.v`: top-level; instancia FD + UC e módulos de debug (7-seg).
  - `verilog/sobel_uc.v`: **FSM** de alto nível:
    - `recebe` (habilita RX) → `processa` (habilita cálculo) → `transmite` (habilita TX).
  - `verilog/sobel_fd.v`: amarra UART RX/TX ao `sobel_processing_unit`.
  - `verilog/sobel_processing_unit_fd.v`: datapath de buffers + kernel:
    - `buffer_raw` (framebuffer entrada)
    - `kernel_sobel` (processamento streaming)
    - `buffer_sobel` (framebuffer saída)
- **Contrato de dados (wire-level)**
  - `rx_serial` → `rx_serial_8N1` → `rx_dados_ascii[7:0]` com `rx_pronto`
  - `tx_dados[7:0]` + `tx_partida` → `tx_serial_8N1` → `tx_saida_serial`
  - `fim_imagem` sinaliza fim do frame tanto na fase de recepção quanto na de transmissão/processamento.
- **UART**
  - RX: `verilog/rx_serial_8N1.v` (tick configurado para 115200)
  - TX: `verilog/tx_serial_8N1.v` (tick configurado para 115200)
- **Kernel Sobel (streaming)**
  - `verilog/kernel_sobel.v`: janela 3×3 com **2 line buffers** + shift da janela.
  - Implementa “flush” após o fim da leitura para cuspir os últimos pixels do pipeline.
  - Borda da imagem é forçada a 0.
- **Framebuffers**
  - `verilog/framebuffer_sequencial.v`: memória interna indexada por contadores (coluna/linha) e `fim_imagem`.

### `pipeline-sobel-fpga/src/` — Protótipos de transceiver (legado)

- **Status**: protótipo/POC anterior ao `after-app/python/worker.py` (útil para testes de link serial e pipeline “frame-a-frame”).
- **Entrypoint**
  - `pipeline-sobel-fpga/src/main.py` com `--role duplex` para “PC → FPGA → PC”.
- **Peças internas**
  - `transceiver.py`: thread que lê serial e acumula bytes (`img_buffer`) até completar um frame (160×120).
  - `img_utils.py`: resize→grayscale via PIL e salvar frames recebidos (`rx_frames/frame_XXXX.png`).
  - `video_utils.py`: captura webcam e conversão frames↔vídeo (para testes manuais).

### `pipeline-sobel-software-only/` — POC (Sobel em software)

- **Objetivo**: validar visualmente o efeito Sobel sem FPGA.
- **Entrypoint**
  - `pipeline-sobel-software-only/main.py`
- **Como funciona**
  - Captura webcam, reduz para 160×120, aplica Sobel via OpenCV.
  - Publica o resultado como câmera virtual via `pyvirtualcam`.

### `video-feed-stub/` — POC (fonte sintética em v4l2loopback)

- **Objetivo**: gerar um feed determinístico para testar consumidores (sem webcam/FPGA).
- **Entrypoint**
  - `video-feed-stub/main.py /dev/videoX`
- **Como funciona**
  - Gera uma forma em movimento, aplica Sobel e publica no device via `pyfakewebcam`.

### `delta-visualization/` — Ferramenta (heatmap por delta temporal)

- **Objetivo**: consumir um device de vídeo (sobel real ou stub) e visualizar um heatmap acumulado por delta (com decaimento).
- **Entrypoint**
  - `delta-visualization/main.py <device_index>`
- **Como funciona**
  - Lê frames, calcula `absdiff` com frame anterior, aplica decaimento e colormap; mostra lado-a-lado.

### `fpga/` — placeholder

- Atualmente vazio; pode ser usado no futuro para artefatos de build, pinouts, scripts de programação, etc.

---

## Como ler o código (caminho recomendado)

Se você quer entender o sistema em 20–40 minutos:

1. **Comece pela UI e o contrato de sessão**
   - `after-app/src/views/RecordView.jsx`
   - `after-app/preload.js`
2. **Vá para o pipeline/worker**
   - `after-app/python/worker.py`
3. **Entenda a interface e o HDL no FPGA**
   - `pipeline-sobel-fpga/quartus/verilog/sobel.v`
   - `pipeline-sobel-fpga/quartus/verilog/sobel_uc.v`
   - `pipeline-sobel-fpga/quartus/verilog/sobel_processing_unit_fd.v`
   - `pipeline-sobel-fpga/quartus/verilog/kernel_sobel.v`

---

## Como rodar (mínimo para desenvolvimento local)

### 1) Rodar a UI (Electron)

Dentro de `after-app/`:

```bash
npm install
npm run build
```

Para abrir o Electron:

```bash
npm run electron
```

Atalho equivalente:

```bash
npm run start
```

> Nota: o Electron carrega `after-app/dist/index.html` (build do Vite). O `npm run dev` (servidor do Vite) não é usado automaticamente pelo Electron neste repo.

### 2) Rodar o worker (Python)

Dentro de `after-app/python/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python worker.py
```

**Notas**:
- O worker tenta auto-descobrir a porta (`/dev/ttyUSB*`, `/dev/ttyACM*`).
- Apenas um processo pode abrir a porta serial por vez.
- O processamento é local (sem internet) e os resultados aparecem na UI quando `heatmap.webm`/`analytics.json` forem gerados.

---

## FPGA/HDL (visão high-level) e projeto Quartus

### Projeto Quartus “final” (QAR)

O arquivo arquivado do projeto Quartus considerado final é:

- `pipeline-sobel-fpga/quartus/sobel_2_g.qar`

**Restaurar/abrir no Quartus**: use o fluxo padrão de “Restore Archive” do Quartus para extrair o projeto e então compile/programa a DE10‑Lite (50 MHz).  
> A documentação aqui é propositalmente de alto nível; o QAR preserva as configurações e arquivos do projeto.

### Pipeline HDL (alto nível)

Em termos de comportamento, o FPGA executa este ciclo:

1. **Recepção (UART RX)**: recebe bytes e preenche o framebuffer “raw”.
2. **Processamento**: `kernel_sobel` lê pixels sequencialmente e gera um pixel Sobel por ciclo (após latência inicial), com flush para completar a imagem.
3. **Transmissão (UART TX)**: transmite o framebuffer de saída (Sobel) de volta ao PC.

Pontos de design relevantes:

- **Streaming + buffers**: o `kernel_sobel` implementa uma janela 3×3 via **line buffers** e shift registers.
- **Tratamento de bordas**: pixels de borda são forçados a zero.
- **Delimitação de frame**: contadores de coluna/linha no `framebuffer_sequencial` determinam `fim_imagem`.
- **Controle**: `sobel_uc.v` coordena os estados “recebe → processa → transmite”.

---

## POCs (contexto histórico e uso opcional)

Estas provas de conceito validaram o efeito final e o “valor” do Sobel antes da implementação em hardware.

### `video-feed-stub/` (Linux / v4l2loopback)

Publica um feed sintético em um device `/dev/videoX` (câmera fake), simulando uma fonte.

Arquivo principal: `video-feed-stub/main.py`

### `pipeline-sobel-software-only/`

Aplica Sobel em software e publica o resultado como câmera virtual.

Arquivo principal: `pipeline-sobel-software-only/main.py`

### `delta-visualization/`

Consome um device de vídeo e gera um heatmap por delta temporal (útil para validar visualmente padrões de movimento).

Arquivo principal: `delta-visualization/main.py`

---

## Operação/uso (para contexto)

Para a operação (clínica/usuário final), consulte:

- `after-app/docs/manual_usuario.md`

