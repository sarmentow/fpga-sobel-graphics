module sobel(
	input clock,
	input reset,
	
	input rx_serial,
	
	output tx_saida_serial,
	
	output [3:0] db_estado,
	output [6:0] dbhex0,
	output [6:0] dbhex1,
	output [6:0] dbhex2,
	output [6:0] dbhex3
);
	wire sobel_calcula, sobel_fim_imagem, tx_pronto, rx_pronto;
	wire tx_partida;
	wire tx_enable, rx_enable;
	wire [7:0] db_rx_dado, db_tx_dado;
	wire reset_uc;
		
	sobel_fd fd(
		.clock(clock),
		.reset(reset | reset_uc),
		.rx_serial(rx_serial),
		.rx_enable(rx_enable),
		.rx_pronto_out(rx_pronto),
		.rx_db_dados_ascii(db_rx_dado),
		.rx_db_estado(),
		.sobel_calcula(sobel_calcula),
		.sobel_fim_imagem(sobel_fim_imagem),
		.tx_partida(tx_partida),
		.tx_enable(tx_enable),
		.tx_saida_serial(tx_saida_serial),
		.tx_pronto(tx_pronto),
		.tx_db_saida_serial(),
		.tx_db_estado(),
		.tx_db_dado(db_tx_dado)
	);
	
	sobel_uc uc(
		.clock(clock),
		.reset(reset),
		.sobel_calcula(sobel_calcula),
		.sobel_fim_imagem(sobel_fim_imagem),
		.tx_partida(tx_partida),
		.tx_pronto(tx_pronto),
		.rx_pronto(rx_pronto),
		.rx_enable(rx_enable),
		.tx_enable(tx_enable),
		.clean_framebuffer_counters(reset_uc),
		.db_estado(db_estado)
	);
	
	hexa7seg hexadb0(
	 .hexa(db_rx_dado[3:0]),
    .display(dbhex0)
	);
	
	hexa7seg hexadb1(
	 .hexa(db_rx_dado[7:4]),
    .display(dbhex1)
	);
	
	hexa7seg hexadb2(
	 .hexa(db_tx_dado[3:0]),
    .display(dbhex2)
	);
	
	hexa7seg hexadb3(
	 .hexa(db_tx_dado[7:4]),
    .display(dbhex3)
	);

	
	
endmodule