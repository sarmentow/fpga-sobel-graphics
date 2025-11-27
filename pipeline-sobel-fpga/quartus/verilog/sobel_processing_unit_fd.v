module sobel_processing_unit_fd #(
    parameter HEIGHT = 120, 
    parameter WIDTH = 160
)(
    input wire clock,
    input wire reset,
    input wire [7:0] rx_dados,
    input wire rx_pronto,
    input wire tx_pronto,
    input wire calcula,
	 input wire tx_enable,
    output wire fim_imagem,
    output wire [7:0] tx_dados
);

    wire fim_imagem_raw;
    wire fim_imagem_sobel;
    wire [7:0] dado_lido_raw;
    wire [7:0] dados_processados_sobel;
    
    wire kernel_ler_pixel;    
    wire kernel_pixel_pronto; 

    assign fim_imagem = (calcula | tx_enable) ? fim_imagem_sobel : fim_imagem_raw;

	 
    framebuffer_sequencial #(
        .WIDTH(WIDTH),
        .HEIGHT(HEIGHT),
        .DATA_WIDTH(8)
    ) buffer_raw (
        .clock(clock),
        .reset(reset),
        
        .incrementa(rx_pronto | kernel_ler_pixel), 
        .write_enable(rx_pronto),
        
        .data_in(rx_dados),
        .data_out(dado_lido_raw), 
        
        .fim_imagem(fim_imagem_raw)
    );

    kernel_sobel #(
        .WIDTH(WIDTH),
        .HEIGHT(HEIGHT)
    ) sobel_core (
        .clock(clock),
        .reset(reset),
        .enable(calcula),             
        .raw_pixel_in(dado_lido_raw), 
        
        .pixel_out(dados_processados_sobel), 
        .ler_pixel(kernel_ler_pixel),       
        .pixel_pronto(kernel_pixel_pronto)  
    );

    framebuffer_sequencial #(
        .WIDTH(WIDTH),
        .HEIGHT(HEIGHT),
        .DATA_WIDTH(8)
    ) buffer_sobel (
        .clock(clock),
        .reset(reset),
        
        .incrementa(kernel_pixel_pronto | tx_pronto),
        .write_enable(kernel_pixel_pronto),
        
        .data_in(dados_processados_sobel),
        .data_out(tx_dados),
        
        .fim_imagem(fim_imagem_sobel)
    );

endmodule