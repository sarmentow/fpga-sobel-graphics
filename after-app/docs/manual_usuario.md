# Manual de Operação Clínica - AFTER

**Sistema de Análise de Padrões Motores e Estereotipias**

## 1. Introdução

O **AFTER** é uma ferramenta de apoio diagnóstico e terapêutico desenvolvida para auxiliar profissionais de saúde na observação e quantificação de padrões de movimento.

Focado no atendimento a pessoas no espectro autista, o sistema utiliza visão computacional para registrar sessões e gerar dados objetivos sobre movimentos repetitivos (estereotipias), "stimming" (autoestimulação) e coordenação motora. O software transforma gravações de vídeo em mapas de calor e gráficos de ritmo, permitindo acompanhar a evolução do paciente e identificar gatilhos comportamentais com precisão matemática.

---

## 2. Preparação do Ambiente

Antes de receber o paciente, certifique-se de que o ambiente de captura está pronto:

1.  **Iluminação:** O ambiente deve estar bem iluminado para garantir a precisão da leitura dos movimentos.
2.  **Posicionamento:** A câmera deve estar fixa (em tripé ou suporte), enquadrando o corpo inteiro do paciente ou a área de interesse (ex: apenas tronco e mãos, se o foco for *flapping*).
3.  **Conexão:** Verifique se a **Unidade de Processamento Externa** (a caixa preta com a placa FPGA) está conectada ao computador via USB. Ela é o "cérebro" que processa os dados de movimento em tempo real.

---

## 3. Realizando uma Sessão (Aba "Gravar")

Ao abrir o software, você será apresentado à tela de **Gravação**.

1.  **Enquadramento:** Verifique na tela se o paciente está visível. Evite muitas pessoas ou objetos em movimento ao fundo, pois isso pode interferir na análise.
2.  **Iniciar Captura:** Quando o comportamento de interesse começar (ou ao iniciar a atividade terapêutica), clique no botão **"Gravar"** (círculo vermelho).
3.  **Durante a Sessão:** Realize a interação normalmente. O sistema é não-invasivo e não requer sensores presos ao corpo do paciente.
4.  **Finalizar:** Clique no botão **"Parar"** para encerrar. O vídeo será salvo automaticamente e enviado para a fila de processamento.

> **Dica Clínica:** Recomenda-se gravar sessões curtas (1 a 5 minutos) focadas em eventos específicos para facilitar a revisão posterior.

---

## 4. Gerenciamento de Histórico (Aba "Sessões")

Nesta tela, você encontra o prontuário digital das gravações realizadas.

*   **Lista de Sessões:** As gravações são organizadas por data e hora.
*   **Status do Processamento:**
    *   *Processando:* O sistema está calculando os dados matemáticos do movimento. Isso pode levar alguns minutos dependendo da duração do vídeo.
    *   *Pronto (Done):* A análise está completa e disponível para visualização.
    *   *Erro:* Houve uma falha técnica (comunique o suporte de TI).

Clique em uma sessão com status **"Pronto"** para abrir o relatório detalhado.

---

## 5. Interpretando os Resultados (Aba "Reproduzir")

Esta é a área de análise clínica. O software cruza o vídeo original com dados quantitativos.

### 5.1 Mapa de Calor (Heatmap)
Ao lado (ou sobreposto) ao vídeo original, você verá uma versão colorida.
*   **O que é:** Representa a amplitude e a localização do movimento.
*   **Interpretação:** Áreas em cores quentes (laranja/vermelho) indicam onde o movimento foi mais intenso. Isso ajuda a diferenciar, por exemplo, se a agitação motora é focal (apenas mãos) ou global (tronco e membros).

### 5.2 Gráfico de Linha do Tempo (Timeline)
Localizado na parte inferior.
*   **Picos:** Mostram os momentos exatos de maior intensidade. Você pode correlacionar esses picos com eventos no vídeo (ex: "O pico de intensidade ocorreu 2 segundos após a introdução do estímulo sonoro").

### 5.3 Métricas de Repetição (Dados Quantitativos)

No painel lateral, o sistema apresenta os biomarcadores do movimento:

*   **Ciclos por Minuto (CPM):**
    *   Mede a velocidade da repetição.
    *   *Uso Clínico:* Útil para monitorar se uma estereotipia está se tornando mais rápida (aguda) ou mais lenta ao longo do tratamento.
*   **Regularidade do Ritmo (0 a 1):**
    *   Indica o quão "robótico" ou consistente é o movimento.
    *   *Valor próximo de 1:* Movimento muito rítmico e constante (comum em *rocking* ou *flapping* sustentado).
    *   *Valor baixo:* Movimento caótico ou esporádico.
*   **Zonas Ativas (Hot Zones):**
    *   Percentual de movimento por quadrante (Superior Esquerdo, Centro, etc).
    *   *Uso Clínico:* Ajuda a documentar lateralidade ou mudanças na postura.

---

## 6. Perguntas Frequentes

**O sistema precisa de internet?**
Não. Todo o processamento é feito localmente no computador e na unidade externa (FPGA) para garantir a privacidade total dos dados do paciente.

**A luz do ambiente afeta o resultado?**
Sim. Ambientes muito escuros podem dificultar a detecção de movimentos sutis. Prefira luz natural ou salas bem iluminadas.

**Posso exportar o vídeo?**
Os vídeos ficam salvos na pasta de sessões do computador e podem ser anexados a prontuários externos se necessário (consulte o suporte de TI para acesso aos arquivos brutos).

---

### Nota para a Equipe de TI/Suporte Técnico

Se o software não iniciar ou apresentar erros de conexão:
1.  Verifique se o **driver da FPGA** está corretamente instalado.
2.  Certifique-se de que o script `worker.py` (backend) está rodando em segundo plano antes de abrir a interface gráfica.
3.  O sistema requer permissões de acesso à **Webcam** e portas **USB/Serial**.
