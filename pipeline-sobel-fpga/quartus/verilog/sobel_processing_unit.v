module sobel_processing_unit(
		input clock,
		input reset,
		input [7:0] rx_dados,
		input rx_pronto,
		input tx_pronto,
		input calcula,
		output fim_imagem,
		output [7:0] tx_dados
);	
	sobel_processing_unit_fd fd(
		.clock(clock),
		.reset(reset),
		.rx_dados(rx_dados),
		.rx_pronto(rx_pronto),
		.tx_pronto(tx_pronto),
		.calcula(calcula),
		.fim_imagem(fim_imagem),
		.tx_dados(tx_dados)
	);
	sobel_processing_unit_uc uc();
endmodule