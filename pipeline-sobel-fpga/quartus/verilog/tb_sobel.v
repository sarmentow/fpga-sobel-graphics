`timescale 1ns / 1ps

module tb_sobel;

    // ========================================================================
    // PARAMETERS (Adjust these to match your hardware design)
    // ========================================================================
    parameter CLK_FREQ   = 50_000_000; // 50 MHz
    parameter BAUD_RATE  = 115200;     // Standard UART Baud Rate
    parameter BIT_PERIOD = 1000000000 / BAUD_RATE; // ns per bit (approx 8680ns)
    
    // ========================================================================
    // SIGNALS
    // ========================================================================
    reg clock;
    reg reset;
    reg rx_serial;          // Input to FPGA (Simulated TX)
    wire tx_saida_serial;   // Output from FPGA (Simulated RX)
    wire [3:0] db_estado;

    // ========================================================================
    // INSTANCE (Unit Under Test)
    // ========================================================================
    sobel uut (
        .clock(clock),
        .reset(reset),
        .rx_serial(rx_serial),
        .tx_saida_serial(tx_saida_serial),
        .db_estado(db_estado)
    );

    // ========================================================================
    // CLOCK GENERATION
    // ========================================================================
    initial clock = 0;
    always #10 clock = ~clock; // 20ns period = 50MHz

    // ========================================================================
    // TEST PROCEDURE
    // ========================================================================
    initial begin
        // 1. Initialization
        reset = 1;
        rx_serial = 1; // UART Idle state is HIGH
        
        $display("=== Simulation Start ===");
        $display("Baud Rate: %d", BAUD_RATE);
        $display("Bit Period: %d ns", BIT_PERIOD);

        // 2. Reset Pulse
        #100;
        reset = 0;
        #100;

        // 3. Send Image Data (Simulating PC sending bytes to FPGA)
        // Assuming 2x4 Image (4 Bytes total based on previous context)
        
        uart_send_byte(8'h1);
        
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
// -- IMAGEM 2

        #(1000)


                uart_send_byte(8'h1);
        
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);
		  
		  uart_send_byte(8'h1);
  
        uart_send_byte(8'h2);
        
        uart_send_byte(8'h3);
        
        uart_send_byte(8'h4);

        #(1000)

        $display("[Info] All data sent. Waiting for processing and response...");

        // 4. Wait for processing and response
        // The UC should automatically detect end of image, calculate, and TX back.
        // We wait enough time for 4 bytes to be received back + calculation time.
        #(BIT_PERIOD * 50 * 6); 

        $display("=== Simulation End ===");
        $stop;
    end

    // ========================================================================
    // PARALLEL PROCESS: MONITOR OUTPUT (Simulated PC Receiving)
    // ========================================================================
    // This block sits and watches the tx_saida_serial line constantly.
    reg [7:0] rx_byte_captured;
    
    initial begin
        forever begin
            // 1. Wait for Start Bit (Falling Edge)
            @(negedge tx_saida_serial);
            
            // 2. Wait half a bit period to center the sampling point
            #(BIT_PERIOD / 2);
            
            // 3. Verify it is still low (valid start bit)
            if (tx_saida_serial == 0) begin
                // Move to first data bit
                #(BIT_PERIOD); 
                
                // Sample 8 bits (LSB First)
                rx_byte_captured[0] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[1] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[2] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[3] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[4] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[5] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[6] = tx_saida_serial; #(BIT_PERIOD);
                rx_byte_captured[7] = tx_saida_serial; #(BIT_PERIOD);
                
                // Stop Bit (should be high)
                if (tx_saida_serial == 1) begin
                    $display("[UART RX] Received Byte: %h at time %t", rx_byte_captured, $time);
                end else begin
                    $display("[UART RX] Framing Error (Stop bit missing) at time %t", $time);
                end
            end
        end
    end

    // ========================================================================
    // TASK: UART SEND (Emulates sending a byte into the FPGA)
    // ========================================================================
    task uart_send_byte;
        input [7:0] data;
        integer i;
        begin
            // Start Bit (Low)
            rx_serial = 0;
            #(BIT_PERIOD);
            
            // Data Bits (LSB First)
            for (i=0; i<8; i=i+1) begin
                rx_serial = data[i];
                #(BIT_PERIOD);
            end
            
            // Stop Bit (High)
            rx_serial = 1;
            #(BIT_PERIOD);
            
            // Small delay between bytes (optional)
            #(BIT_PERIOD * 2);
        end
    endtask

endmodule