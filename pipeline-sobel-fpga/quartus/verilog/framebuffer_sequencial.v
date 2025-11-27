module framebuffer_sequencial #(
    parameter WIDTH = 160,
    parameter HEIGHT = 120,
    parameter DATA_WIDTH = 8
)(
    input wire clock,
    input wire reset,
    
    input wire incrementa,     
    input wire write_enable,   
    
    input wire [DATA_WIDTH-1:0] data_in,
    output reg [DATA_WIDTH-1:0] data_out,
    
    output wire fim_imagem
);

    localparam SIZE = WIDTH * HEIGHT;
    localparam COL_BITS = $clog2(WIDTH);
    localparam ROW_BITS = $clog2(HEIGHT);
    localparam ADDR_BITS = $clog2(SIZE);

    reg [DATA_WIDTH-1:0] memory [0:SIZE-1];

    wire [COL_BITS-1:0] coluna;
    wire [ROW_BITS-1:0] fileira;
    wire fim_conta_coluna;
    wire fim_conta_fileira;
    wire [ADDR_BITS-1:0] addr_atual;

    assign addr_atual = (fileira * WIDTH) + coluna;
    assign fim_imagem = fim_conta_coluna & fim_conta_fileira;

    contador_m #(.M(WIDTH), .N(COL_BITS)) cnt_col (
        .clock(clock), 
        .zera_as(reset), 
        .zera_s(1'b0),
        .conta(incrementa), 
        .Q(coluna), 
        .fim(fim_conta_coluna), 
        .meio()
    );
      
    contador_m #(.M(HEIGHT), .N(ROW_BITS)) cnt_row (
        .clock(clock), 
        .zera_as(reset), 
        .zera_s(1'b0),
        .conta(fim_conta_coluna & incrementa), 
        .Q(fileira), 
        .fim(fim_conta_fileira), 
        .meio()
    );

    always @(posedge clock) begin
        data_out <= memory[addr_atual];

        if (write_enable) begin
            memory[addr_atual] <= data_in;
        end
    end

endmodule