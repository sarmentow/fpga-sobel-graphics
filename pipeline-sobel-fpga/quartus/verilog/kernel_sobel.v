module kernel_sobel #(
    parameter WIDTH = 160, 
    parameter HEIGHT = 120
)(
    input wire clock,
    input wire reset,
    input wire enable,              
    input wire [7:0] raw_pixel_in,  
    
    output reg [7:0] pixel_out,     
    output reg ler_pixel,           
    output reg pixel_pronto         
);

    // Definições de contagem
    localparam TOTAL_PIXELS = WIDTH * HEIGHT;
    localparam DATA_WIDTH = 8;
    // Latência: 2 linhas completas + 2 pixels do shift register da linha atual
    localparam LATENCIA_INICIAL = (2 * WIDTH) + 2;

    // Line Buffers
    reg [DATA_WIDTH-1:0] line_buffer_0 [0:WIDTH-1];
    reg [DATA_WIDTH-1:0] line_buffer_1 [0:WIDTH-1];
    reg [$clog2(WIDTH)-1:0] x_write_ptr;

    // Janela 3x3
    reg [DATA_WIDTH-1:0] w [0:2][0:2];

    // Contadores Principais
    reg [$clog2(TOTAL_PIXELS+1)-1:0] pixels_lidos_cnt;      // Conta inputs (max TOTAL_PIXELS)
    reg [$clog2(TOTAL_PIXELS+LATENCIA_INICIAL+1)-1:0] shifts_cnt; // Conta ciclos de processamento
    
    // Coordenadas virtuais de saída
    reg [$clog2(WIDTH)-1:0]  col_out;
    reg [$clog2(HEIGHT)-1:0] row_out;

    // Sinais de Controle
    wire deve_shiftar;
    wire pipeline_cheio;
    wire terminou_imagem;
    reg [7:0] dado_entrada_mux;

    // -------------------------------------------------------------------------
    // Lógica de Controle de Fluxo (Flush)
    // -------------------------------------------------------------------------
    
    // O processamento termina apenas quando geramos todas as saídas (TOTAL_PIXELS),
    // não quando terminamos de ler. Sabemos que geramos 1 saida por shift após a latência.
    assign terminou_imagem = (shifts_cnt >= (TOTAL_PIXELS + LATENCIA_INICIAL));
    
    // Continuamos trabalhando enquanto habilitado e não terminamos de cuspir a imagem
    assign deve_shiftar = enable && !terminou_imagem;

    // Só lemos da memória externa se ainda há pixels lá
    always @(*) begin
        if (deve_shiftar && (pixels_lidos_cnt < TOTAL_PIXELS))
            ler_pixel = 1'b1;
        else
            ler_pixel = 1'b0;
    end

    // Se estamos na fase de Flush (lendo além do fim da imagem), injetamos 0 (preto)
    // para limpar o pipeline corretamente.
    always @(*) begin
        if (ler_pixel) 
            dado_entrada_mux = raw_pixel_in;
        else 
            dado_entrada_mux = 8'd0;
    end

    // -------------------------------------------------------------------------
    // Pipeline: Line Buffers e Janela
    // -------------------------------------------------------------------------
    always @(posedge clock) begin
        if (reset) begin
            pixels_lidos_cnt <= 0;
            shifts_cnt <= 0;
            x_write_ptr <= 0;
        end else if (deve_shiftar) begin
            // Contador de Leitura
            if (ler_pixel)
                pixels_lidos_cnt <= pixels_lidos_cnt + 1;
            
            // Contador de Deslocamentos (Ciclos de trabalho)
            shifts_cnt <= shifts_cnt + 1;

            // --- Shift da Janela ---
            w[0][0] <= w[0][1]; w[0][1] <= w[0][2];
            w[1][0] <= w[1][1]; w[1][1] <= w[1][2];
            w[2][0] <= w[2][1]; w[2][1] <= w[2][2];

            // Atualiza coluna 2 (Entrada)
            w[0][2] <= line_buffer_0[x_write_ptr]; 
            w[1][2] <= line_buffer_1[x_write_ptr];
            w[2][2] <= dado_entrada_mux; // Usa o MUX (Dado Real ou Zero de Flush)

            // Rotaciona Line Buffers
            line_buffer_0[x_write_ptr] <= line_buffer_1[x_write_ptr];
            line_buffer_1[x_write_ptr] <= dado_entrada_mux;

            // Ponteiro circular X
            if (x_write_ptr == WIDTH-1)
                x_write_ptr <= 0;
            else
                x_write_ptr <= x_write_ptr + 1;
        end
    end

    // -------------------------------------------------------------------------
    // Geração de Saída (Coordenadas e Pixel Pronto)
    // -------------------------------------------------------------------------
    
    // O pipeline está cheio quando fizemos shifts suficientes para o pixel (1,1) chegar ao centro
    assign pipeline_cheio = (shifts_cnt >= LATENCIA_INICIAL);

    always @(posedge clock) begin
        if (reset) begin
            col_out <= 0;
            row_out <= 0;
            pixel_pronto <= 0;
        end else begin
            // Só geramos saída válida se o pipeline encheu E ainda estamos shiftando
            if (deve_shiftar && pipeline_cheio) begin
                pixel_pronto <= 1'b1;
                
                // Atualiza coordenadas de SAÍDA
                if (col_out == WIDTH-1) begin
                    col_out <= 0;
                    row_out <= row_out + 1;
                end else begin
                    col_out <= col_out + 1;
                end
            end else begin
                pixel_pronto <= 1'b0;
            end
        end
    end

    // -------------------------------------------------------------------------
    // Cálculo do Sobel (Combinacional) - Inalterado
    // -------------------------------------------------------------------------
    integer gx, gy, abs_gx, abs_gy, soma_abs;
    
    always @(*) begin
        pixel_out = 8'b00000000;
        
        // Tratamento de Borda: Força preto
        if (row_out == 0 || row_out == HEIGHT-1 || col_out == 0 || col_out == WIDTH-1) begin
            pixel_out = 8'd0;
        end else begin
            // Math: Gx
            gx = (w[0][2] + 2*w[1][2] + w[2][2]) - (w[0][0] + 2*w[1][0] + w[2][0]);
            // Math: Gy
            gy = (w[0][0] + 2*w[0][1] + w[0][2]) - (w[2][0] + 2*w[2][1] + w[2][2]);

            abs_gx = (gx < 0) ? -gx : gx;
            abs_gy = (gy < 0) ? -gy : gy;
            soma_abs = abs_gx + abs_gy;

            if (soma_abs > 255) pixel_out = 8'd255;
            else pixel_out = soma_abs[7:0];
        end
    end

endmodule