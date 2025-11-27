module sobel_uc(
	input clock,
	input reset,
	input sobel_fim_imagem,
	input tx_pronto,
	input rx_pronto,
	output reg sobel_calcula,
	output reg rx_enable,
	output reg tx_enable,
	output reg tx_partida,
	output reg clean_framebuffer_counters,
	output reg [3:0] db_estado
);
	parameter inicial = 4'b0000; 
	parameter recebe = 4'b0001;
	parameter processa = 4'b0010;
	parameter memory_hold_transmite = 4'b0011;
	parameter prepara_transmite = 4'b0100;
	parameter transmite = 4'b0101;
	
    reg [3:0] Eatual, Eprox;

    always @(posedge clock or posedge reset) begin
        if (reset)
            Eatual <= inicial;
        else
            Eatual <= Eprox;
    end

    always @* begin
        case (Eatual)
            inicial: Eprox = recebe;
            recebe: Eprox = (sobel_fim_imagem & rx_pronto) ? processa : recebe;
            processa: Eprox = (sobel_fim_imagem) ? memory_hold_transmite : processa;
            memory_hold_transmite: Eprox = prepara_transmite;
				prepara_transmite: Eprox = transmite;
            transmite: Eprox = (sobel_fim_imagem & tx_pronto) ? inicial : (tx_pronto ? prepara_transmite : transmite); 
            default: Eprox = inicial; 
        endcase
    end

    // Logica de saida (maquina de Moore)
    always @* begin
		  sobel_calcula = (Eatual == processa) ? 1'b1 : 1'b0;
		  rx_enable = (Eatual == recebe) ? 1'b1 : 1'b0;
		  tx_enable = (Eatual == prepara_transmite || Eatual == transmite) ? 1'b1 : 1'b0;
		  tx_partida = (Eatual == prepara_transmite) ? 1'b1 : 1'b0;
		  clean_framebuffer_counters = (Eatual == inicial) ? 1'b1 : 1'b0;

        // Saida de depuracao (estado)
        case (Eatual)
            inicial: db_estado = 4'd0;
            recebe: db_estado = 4'd1; 
            processa: db_estado = 4'd2; 
				memory_hold_transmite: db_estado = 4'd3;
            prepara_transmite   : db_estado = 4'd4; 
            transmite: db_estado = 4'd5; 
            default: db_estado = 4'b1110; // E
        endcase
    end
endmodule