`timescale 1ns / 1ps

// -------------------------------------------------------------------------
// Main Testbench
// -------------------------------------------------------------------------
module tb_sobel_processing_unit_fd;

    // Parameters matches the DUT default or override
    parameter HEIGHT = 2;
    parameter WIDTH = 4;

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

    // Internal loop variable
    integer i;

    // Instantiate the Unit Under Test (UUT)
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

    // Clock Generation (10ns period)
    always #5 clock = ~clock;

    // Test Procedure
    initial begin
        // 1. Initialize Inputs
        clock = 0;
        reset = 1;
        rx_dados = 0;
        rx_pronto = 0;
        tx_pronto = 0;
        calcula = 0;

        // Wait for global reset
        #20;
        reset = 0;
        #10;

        $display("=== Starting Simulation ===");
        $display("Config: HEIGHT=%d, WIDTH=%d", HEIGHT, WIDTH);
        // Note: WIDTH=4 means 2 bytes per row (since 2 pixels per byte).
        // Total bytes to send = (WIDTH/2) * HEIGHT = 2 * 2 = 4 bytes.

        // ------------------------------------------------------------
        // PHASE 1: LOAD IMAGE (RX)
        // ------------------------------------------------------------
        $display("\n[Phase 1] Loading Data via rx_dados...");
        
        // We will send patterns: 8'hA5, 8'h12, 8'hF0, 8'h0F
        // Sequence should wrap naturally: (0,0) -> (0,1) -> (1,0) -> (1,1) -> Wrap to (0,0)
        
        send_byte(8'hA5); // 1010 0101 (Step 1)
        send_byte(8'h12); // 0001 0010 (Step 2)
        send_byte(8'hF0); // 1111 0000 (Step 3)
        
        // After sending 3 bytes, we are at the last position. 
        // We check if fim_imagem goes high during the 4th byte write indicating end of frame.
        send_byte(8'h0F); // 0000 1111 (Step 4 - Should wrap counter after this)

        // Note: fim_imagem depends on the current counter state. 
        // If logic is correct, it might pulse high during the last step.
        // Since we are relying on wrap-around, we proceed directly.
        $display("-> Loading complete. Counters should be wrapped to 0.");

        // ------------------------------------------------------------
        // PHASE 2: CALCULATE (Invert Data)
        // ------------------------------------------------------------
        $display("\n[Phase 2] Calculating (Inverting Bits)...");
        
        // We perform the calculation 4 times to traverse the whole image again.
        // This will wrap the counters from (0,0) back to (0,0) by the end.
        
        calcula = 1;
        
        for (i = 0; i < 4; i = i + 1) begin
            // Wait one clock cycle per address to allow write & counter increment
            @(posedge clock);
            #1; // wait past hold time
        end
        
        calcula = 0;
        $display("-> Calculation loop finished. Counters should be wrapped to 0.");

        // ------------------------------------------------------------
        // PHASE 3: READ RESULTS (TX)
        // ------------------------------------------------------------
        $display("\n[Phase 3] Reading Results...");
        
        // Check 1: Input A5 (1010 0101) -> Expect 5A (0101 1010)
        verify_output(8'h5A); 
        
        // Check 2: Input 12 (0001 0010) -> Expect ED (1110 1101)
        verify_output(8'hED);

        // Check 3: Input F0 (1111 0000) -> Expect 0F (0000 1111)
        verify_output(8'h0F);

        // Check 4: Input 0F (0000 1111) -> Expect F0 (1111 0000)
        verify_output(8'hF0);

        $display("\n=== Simulation Complete ===");
        $finish;
    end

    // Task to send a byte
    task send_byte;
        input [7:0] data;
        begin
            @(negedge clock); // Setup data before clock edge
            rx_dados = data;
            rx_pronto = 1;
            @(posedge clock); // Wait for write logic
            #1; // Hold slightly past edge
            // Check for End of Image signal on the last byte (optional verification)
            if (fim_imagem) $display("   [Info] fim_imagem asserted at data %h", data);
            
            rx_pronto = 0;
            #9; 
        end
    endtask

    // Task to verify output and advance tx
    task verify_output;
        input [7:0] expected;
        begin
            // 1. Wait for data to be stable at the output (registered output)
            // The logic outputs tx_dados based on current pointers.
            @(negedge clock); 
            
            if (tx_dados !== expected) begin
                $display("FAIL: Time %t | Expected %h, Got %h", $time, expected, tx_dados);
            end else begin
                $display("PASS: Time %t | Got %h", $time, tx_dados);
            end

            // 2. Acknowledge read to advance counter
            tx_pronto = 1;
            @(posedge clock); 
            #1;
            tx_pronto = 0;
            #9;
        end
    endtask

endmodule