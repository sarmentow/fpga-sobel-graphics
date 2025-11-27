module sobel_fd(
	input clock,
	input reset,
	
	input rx_serial,
	input rx_enable,
	// sinais de depuracao
	output [7:0] rx_db_dados_ascii,
	output rx_pronto_out,
	output rx_db_estado,
	output rx_db_dados,
	
	input sobel_calcula,
	output sobel_fim_imagem,
	
	
	input tx_partida,
	input tx_enable,
	output tx_saida_serial,
	output tx_pronto,
	// sinais de depuracao
	output tx_db_saida_serial,
	output [7:0] tx_db_dado,
	output [6:0] tx_db_estado
);
	
	// vai ligar o sobel_processing_unit ao tx
	wire [7:0] tx_dados;	
	wire [7:0] rx_dados_ascii;
	wire rx_pronto;
	
	assign rx_pronto_out = rx_pronto;
	assign rx_db_dados_ascii = rx_dados_ascii;
	assign tx_db_dado = tx_dados;
	assign rx_serial_in = rx_enable ? rx_serial : 1'b1;
	
	tx_serial_8N1 tx(
    .clock(clock),
    .reset(reset),
    .partida(tx_partida),
    .dados_ascii(tx_dados), // entradas
	 
    .saida_serial(tx_saida_serial), // saidas
    .pronto(tx_pronto),
    .db_clock(), // saidas de depuracao
    .db_tick(),
    .db_partida(),
    .db_saida_serial(tx_db_saida_serial),
    .db_estado(tx_db_estado)
	);
	
	
	sobel_processing_unit spu(
		.clock(clock),
		.reset(reset),
		.rx_dados(rx_dados_ascii),
		.rx_pronto(rx_pronto),
		.tx_pronto(tx_pronto),
		.calcula(sobel_calcula),
		.tx_enable(tx_enable),
		
		.fim_imagem(sobel_fim_imagem),
		.tx_dados(tx_dados)
	); 
	
	rx_serial_8N1 rx(
    .clock(clock),
    .reset(reset),
    .RX(rx_serial_in),
    .pronto(rx_pronto),
    .dados_ascii(rx_dados_ascii),
    .db_clock(), // saidas de depuracao
    .db_tick(),
    .db_dados(rx_db_dados), // dados ascii tambem serao exibidos nos displays
    .db_estado(rx_db_estado)
	);	
endmodule