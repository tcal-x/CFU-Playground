// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.



// from ~/lscc/radiant/2.2/cae_library/synthesis/verilog/lifcl.v
/*
module DPSC512K(DIA, DIB, ADA, ADB, CLK, CEA, CEB, WEA, WEB, CSA, CSB, RSTA, RSTB, BENA_N, BENB_N, CEOUTA, CEOUTB, DOA, DOB, ERRDECA, ERRDECB); //synthesis syn_black_box syn_lib_cell=1
    input [31:0] DIA;
    input [31:0] DIB;
    input [13:0] ADA;
    input [13:0] ADB;
    input CLK;
    input CEA;
    input CEB;
    input WEA;
    input WEB;
    input CSA;
    input CSB;
    input RSTA;
    input RSTB;
    input [3:0] BENA_N;
    input [3:0] BENB_N;
    input CEOUTA;
    input CEOUTB;
    output [31:0] DOA;
    output [31:0] DOB;
    output [1:0] ERRDECA;
    output [1:0] ERRDECB;
    parameter OUTREG_A = "NO_REG";
    parameter OUTREG_B = "NO_REG";
    parameter GSR = "ENABLED";
    parameter RESETMODE = "SYNC";

endmodule
*/



module Cfu (
  input               cmd_valid,
  output              cmd_ready,
  input      [9:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,
  output              rsp_valid,
  input               rsp_ready,
  output     [31:0]   rsp_payload_outputs_0,
  input               reset,
  input               clk
);

  reg delay_valid;
  always @(posedge clk) delay_valid <= cmd_valid;

  assign rsp_valid = delay_valid;
  assign cmd_ready = rsp_ready;


  // PORT A: read/write from CFU interface
  wire [31:0] addr_a = cmd_payload_inputs_0;
  wire [31:0] din_a  = cmd_payload_inputs_1;
  wire        wen_a  = cmd_valid & cmd_payload_function_id[0];

  wire [31:0] dout_a;
  assign rsp_payload_outputs_0 = dout_a;



  // PORT B: write every cycle addresses 00 ... ff
  reg [31:0] counter;
  initial counter = 32'd0;
  always @(posedge clk) begin
      counter <= counter + 1;
  end
  wire [31:0] din_b = counter;
  wire [13:0] addr_b = counter[7:0];



  //
  // Memory instantiation
  //
  DPSC512K DPSC512K_0(
     .CLK(clk),
     .DIA(din_a),
     .DIB(din_b),
     .ADA(addr_a),
     .ADB(addr_b),
     .CEA(cmd_valid),
     .CEB(1'b1),
     .WEA(wen_a),
     .WEB(1'b1),
     .CSA(1'b1),
     .CSB(1'b1),
     .RSTA(1'b0),
     .RSTB(1'b0),
     .BENA_N(4'b0000),
     .BENB_N(4'b0000),
     .CEOUTA(cmd_valid),
     .CEOUTB(1'b0),
     .DOA(dout_a),
     .DOB()
  );




endmodule
