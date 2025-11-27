`timescale 1ns / 1ps

module tb_sobel_processing_unit_fd;

    // -------------------------------------------------------------------------
    // Parâmetros (Aumentados para 4x4 para permitir kernel 3x3)
    // -------------------------------------------------------------------------
    parameter HEIGHT = 4;
    parameter WIDTH  = 4;
    parameter TOTAL_PIXELS = HEIGHT * WIDTH;

    // Inputs
    reg clock;
    reg reset;
    reg [7:0] rx_dados;
    reg rx_pronto;
    reg tx_pronto;
    reg calcula;

    // Outputs
    wire fim_imagem;
    wire [7:0] tx_dados;

    // Variáveis de teste
    integer i;

    // Instância do DUT (Device Under Test)
    sobel_processing_unit_fd #(
        .HEIGHT(HEIGHT), 
        .WIDTH(WIDTH)
    ) uut (
        .clock(clock), 
        .reset(reset), 
        .rx_dados(rx_dados), 
        .rx_pronto(rx_pronto), 
        .tx_pronto(tx_pronto), 
        .calcula(calcula), 
        .fim_imagem(fim_imagem), 
        .tx_dados(tx_dados)
    );

    // Geração de Clock (100MHz - período 10ns)
    always #5 clock = ~clock;

    initial begin
        // Inicialização
        clock = 0;
        reset = 1;
        rx_dados = 0;
        rx_pronto = 0;
        tx_pronto = 0;
        calcula = 0;

        // Reset Global
        #20;
        reset = 0;
        #10;

        $display("=== INICIO DA SIMULACAO (Sobel 3x3) ===");
        $display("Config: %dx%d (%d pixels)", WIDTH, HEIGHT, TOTAL_PIXELS);

        // ------------------------------------------------------------
        // FASE 1: CARREGAR IMAGEM (RX)
        // ------------------------------------------------------------
        // Padrão de Teste: "Caixa"
        // 00 00 00 00  (Linha 0 - Borda Preta)
        // 00 FF FF 00  (Linha 1 - Miolo Branco)
        // 00 FF FF 00  (Linha 2 - Miolo Branco)
        // 00 00 00 00  (Linha 3 - Borda Preta)
        
        $display("\n[Fase 1] Carregando Imagem...");
        
        // Linha 0
        send_byte(8'h00); send_byte(8'h00); send_byte(8'h00); send_byte(8'h00);
        // Linha 1
        send_byte(8'h00); send_byte(8'hFF); send_byte(8'hFF); send_byte(8'h00);
        // Linha 2
        send_byte(8'h00); send_byte(8'hFF); send_byte(8'hFF); send_byte(8'h00);
        // Linha 3
        send_byte(8'h00); send_byte(8'h00); send_byte(8'h00); send_byte(8'h00);

        $display("-> Carga completa.");

        // ------------------------------------------------------------
        // FASE 2: PROCESSAMENTO (SOBEL)
        // ------------------------------------------------------------
        $display("\n[Fase 2] Calculando Sobel...");
        
        // Diferença Crucial: 'calcula' agora é um ENABLE. 
        // Devemos mantê-lo alto enquanto o kernel processa a imagem inteira.
        // O Kernel precisa ler todos os pixels para terminar.
        
        calcula = 1;

        // Esperamos tempo suficiente para ler todos os pixels + latência do pipeline
        // Latência aprox: 2 linhas + overhead. Vamos esperar 3x o tempo de pixel para garantir.
        repeat (TOTAL_PIXELS * 3) @(posedge clock);
        
        calcula = 0;
        $display("-> Calculo finalizado (estimado pelo tempo).");

        // ------------------------------------------------------------
        // FASE 3: VERIFICAR RESULTADOS (TX)
        // ------------------------------------------------------------
        $display("\n[Fase 3] Lendo Resultados...");

        // Lógica de verificação:
        // Bordas (Linha 0, 3 e Coluna 0, 3) -> DEVEM ser 0 (Kernel força zero na borda).
        // Miolo (1,1), (1,2), (2,1), (2,2) -> DEVEM detectar a variação 00->FF.
        
        // Linha 0 (Borda Superior) - Tudo 0
        verify_output(8'h00); verify_output(8'h00); verify_output(8'h00); verify_output(8'h00);

        // Linha 1
        // (1,0) Borda Esq -> 0
        verify_output(8'h00); 
        // (1,1) Vizinhos: Esq=00, Dir=FF, Baixo=FF. Gradiente Alto -> 255 (FF)
        verify_output(8'hFF); 
        // (1,2) Vizinhos: Esq=FF, Dir=00. Gradiente Alto -> 255 (FF)
        verify_output(8'hFF); 
        // (1,3) Borda Dir -> 0
        verify_output(8'h00);

        // Linha 2
        // (2,0) Borda Esq -> 0
        verify_output(8'h00); 
        // (2,1) Gradiente Alto -> 255 (FF)
        verify_output(8'hFF); 
        // (2,2) Gradiente Alto -> 255 (FF)
        verify_output(8'hFF); 
        // (2,3) Borda Dir -> 0
        verify_output(8'h00);

        // Linha 3 (Borda Inferior) - Tudo 0
        verify_output(8'h00); verify_output(8'h00); verify_output(8'h00); verify_output(8'h00);

        $display("\n=== Simulacao Completa com Sucesso ===");
        $finish;
    end

    // Tarefa auxiliar para enviar bytes (RX Protocol)
    task send_byte;
        input [7:0] data;
        begin
            @(negedge clock);
            rx_dados = data;
            rx_pronto = 1;
            @(posedge clock); 
            #1; // Hold time
            rx_pronto = 0;
            @(posedge clock); // Wait for recovery
        end
    endtask

    // Tarefa auxiliar para verificar e ler bytes (TX Protocol)
    task verify_output;
        input [7:0] expected;
        begin
            // O dado já deve estar disponível na saída do buffer
            @(negedge clock);
            
            if (tx_dados !== expected) begin
                $display("[ERRO] Pixel %0d: Esperado %h, Recebido %h", i, expected, tx_dados);
            end else begin
                //$display("[OK] Pixel %0d: %h", i, tx_dados);
            end

            // Pulsa tx_pronto para avançar o ponteiro de leitura do buffer
            tx_pronto = 1;
            @(posedge clock);
            #1;
            tx_pronto = 0;
            // Pequeno delay para a memória atualizar o dado de saída
            @(posedge clock);
            
            i = i + 1; // Contador auxiliar de debug
        end
    endtask

endmodule