/* --------------------------------------------------------------------------
 *  Arquivo   : rx_serial_8N1.v
 * --------------------------------------------------------------------------
 *  Descricao : circuito de recepcao serial assincrona
 *              para comunicacao serial 7N1 
 *             (12 bits de dados, sem paridade, 1 stop bit)
 *              
 *  saidas: dados_ascii - display HEX1 e HEX0 e db_dados - leds
 * --------------------------------------------------------------------------
 *  Revisoes  :
 *     Data        Versao  Autor              Descricao
 *     15/10/2024  5.0     Augusto Vaccarelli conversao para receptor
 *     29/10/2024  5.1     Edson Midorikawa   revisao do codigo
 * --------------------------------------------------------------------------
 */ 
 
module rx_serial_8N1 (
    input         clock      ,
    input         reset      ,
    input         RX         ,
    output        pronto     ,
    output [7:0]  dados_ascii,
    output        db_clock   , // saidas de depuracao
    output        db_tick    ,
	 output [13:0] db_dados   , // dados ascii tambem serao exibidos nos displays
    output [6:0]  db_estado       
);
 
    wire       s_reset      ;
    wire       s_zera       ;
    wire       s_zera_tick  ;
    wire       s_registra   ;    
    wire       s_conta      ;
    wire       s_carrega    ;
    wire       s_desloca    ;
    wire       s_tick       ;
    wire       s_meio_tick  ;
    wire       s_fim        ;
    wire [3:0] s_estado     ;
    wire [7:0] s_dados_ascii;

    // sinal reset ativo em alto (chave ou GPIO)
    assign s_reset  = reset;
     
    // fluxo de dados
    rx_serial_8N1_fd U1_FD (
        .clock       ( clock         ),
        .reset       ( s_reset       ),
        .zera        ( s_zera        ),
        .conta       ( s_conta       ),
        .carrega     ( s_carrega     ),
        .desloca     ( s_desloca     ),
        .dados_ascii ( s_dados_ascii ),
        .RX          ( RX            ),
        .registra    ( s_registra    ),
        .fim         ( s_fim         )
    );


    // unidade de controle
    rx_serial_uc U2_UC (
        .clock     ( clock       ),
        .reset     ( s_reset     ),
        .tick      ( s_tick      ),
        .fim       ( s_fim       ),
        .RX        ( RX          ),
        .zera      ( s_zera      ),
        .conta     ( s_conta     ),
        .carrega   ( s_carrega   ),
        .desloca   ( s_desloca   ),
        .pronto    ( pronto      ),
        .registra  ( s_registra  ),
        .zera_tick ( s_zera_tick ),
        .db_estado ( s_estado    )
    );

    // gerador de tick
    // fator de divisao para 9600 bauds (5208=50M/9600) 13 bits
    // fator de divisao para 115.200 bauds (434=50M/115200) 9 bits
    contador_m #(
        // .M(5208),  // 9600 bauds
        // .N(13) 
        .M(434),      // 115200 bauds
        .N(9) 
     ) U3_TICK (
        .clock   ( clock       ),
        .zera_as ( 1'b0        ),
        .zera_s  ( s_zera_tick ),
        .conta   ( 1'b1        ),
        .Q       (             ),
        .fim     (             ),
        .meio    ( s_tick      )   // meio do bit
    );
         
     // saida de dados ascii
     assign dados_ascii = s_dados_ascii;

    // hexa0
    hexa7seg HEX5 ( 
        .hexa    ( s_estado  ), 
        .display ( db_estado )
    );
     
     hexa7seg HEX0 ( 
        .hexa    ( s_dados_ascii [3:0] ), 
        .display ( db_dados [6:0]      )
    );
     
     hexa7seg HEX1 ( 
        .hexa    ( s_dados_ascii [5:4] ), 
        .display ( db_dados [13:7]     )
    );

    // saidas de depuracao
    assign db_clock = clock; 
    assign db_tick  = s_tick; 

endmodule
