/*
 * Copyright (c) 2025 Evan Li
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_counter (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    reg [7:0] counter_bits;
    reg sync_load_prev;

    // set uio to all inputs (but only 0 and 1 are used)
    assign uio_oe = 0;
    assign uio_out = 0;
    assign uo_out = uio_in[1] ? 8'bz : counter_bits;

    // on rst_n falling edge, counter bits set to 0
    // on clock rising edge, increment counter
    // or set counter bits to ui_in if uio_in[0] (load_n) synchronized falling edge
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter_bits <= 8'b0;
            sync_load_prev <= 1'b1;
        end else begin
            prev_sync_load <= uio_in[0];
            if (!uio_in[0] && prev_sync_load) begin // sync falling edge of load_n
                counter_bits <= ui_in;
            end else begin
                counter_bits <= counter_bits + 1;
            end
        end
    end

    // List all unused inputs to prevent warnings
    wire _unused = &{ena, 1'b0};

endmodule
