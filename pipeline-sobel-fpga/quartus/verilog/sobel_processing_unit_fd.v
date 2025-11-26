module sobel_processing_unit_fd#(parameter HEIGHT=2, WIDTH=4)(
        input clock,
        input reset,
        input [7:0] rx_dados,
        input rx_pronto,
        input tx_pronto,
        input calcula,
        output fim_imagem,
        output reg [7:0] tx_dados
);

    // FIX: Split memory into Even and Odd banks to allow simultaneous access
    // Size is WIDTH/2 because each bank holds half the pixels
    reg [3:0] raw_fb_even[HEIGHT-1:0][(WIDTH/2)-1:0]; 
    reg [3:0] raw_fb_odd [HEIGHT-1:0][(WIDTH/2)-1:0];
    
    reg [3:0] sobel_fb_even[HEIGHT-1:0][(WIDTH/2)-1:0];
    reg [3:0] sobel_fb_odd [HEIGHT-1:0][(WIDTH/2)-1:0];

    wire [$clog2(WIDTH)-1:0] coluna; // Note: This is actually the "pair" index
    wire [$clog2(HEIGHT)-1:0] fileira;
    wire fim_conta_coluna, fim_conta_fileira;
    wire incrementa_framebuffer;
    
    assign incrementa_framebuffer = calcula | rx_pronto | tx_pronto;
    assign fim_imagem = fim_conta_coluna & fim_conta_fileira;

    // Counters remain exactly the same
    contador_m #(.M(WIDTH/2), .N($clog2(WIDTH))) contador_coluna (
        .clock(clock), .zera_as(reset), .zera_s(),
        .conta(incrementa_framebuffer), .Q(coluna), 
        .fim(fim_conta_coluna), .meio()
    );
     
    contador_m #(.M(HEIGHT), .N($clog2(HEIGHT))) contador_fileira (
        .clock(clock), .zera_as(reset), .zera_s(),
        .conta(fim_conta_coluna & incrementa_framebuffer), .Q(fileira), 
        .fim(fim_conta_fileira), .meio()
    );
        
    always @ (posedge clock) begin
        // READ: Concatenate the outputs from both banks
        // Note: We use 'coluna' directly, no *2 needed because banks are half-width
        tx_dados <= {sobel_fb_even[fileira][coluna], sobel_fb_odd[fileira][coluna]};

        // WRITE: Raw Data
        if (rx_pronto) begin
            // Write to Odd Bank (Low Nibble)
            raw_fb_odd[fileira][coluna]  <= rx_dados[3:0];
            // Write to Even Bank (High Nibble)
            raw_fb_even[fileira][coluna] <= rx_dados[7:4];
        end
        
        // WRITE: Sobel Calculation
        if (calcula) begin
            // Invert and write to respective banks
            sobel_fb_odd[fileira][coluna]  <= ~raw_fb_odd[fileira][coluna];
            sobel_fb_even[fileira][coluna] <= ~raw_fb_even[fileira][coluna];
        end
    end
endmodule