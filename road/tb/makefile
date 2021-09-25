#hdl testbench makefile
# SIM ?= questa
# TOPLEVEL_LANG ?= vhdl
# COMPILE_ARGS += -2008
# SCRIPT_FILE = wave.do

# VHDL_SOURCES +=  ../hdl/priority_encoder/hdl/priority_encoder.vhd ../hdl/pat_pkg.vhd ../hdl/patterns.vhd ../hdl/pat_unit.vhd
# #use VHDL_SOURCES for VHDL files

# #TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
# #the actual module name
# TOPLEVEL = pat_unit
# #MODULE is the basename of the Python test file
# #name of python files w/o the python extension
# MODULE = pat_unit_tb

# #defaults
# #include cocotb's make rules to take care of the simulator setup
# include $(shell cocotb-config --makefiles)/Makefile.sim

SIM ?= questa
TOPLEVEL_LANG ?= vhdl
COMPILE_ARGS += -2008
SCRIPT_FILE = wave.do

VHDL_SOURCES +=  ../hdl/priority_encoder/hdl/priority_encoder.vhd ../hdl/pat_pkg.vhd ../hdl/patterns.vhd ../hdl/pat_unit.vhd ../hdl/dav_to_phase.vhd ../hdl/pat_unit_mux.vhd
#use VHDL_SOURCES for VHDL files

#TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
#the actual module name
TOPLEVEL = pat_unit_mux
# #MODULE is the basename of the Python test file
# #name of python files w/o the python extension
MODULE = pat_unit_mux_tb

#defaults
#include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim


chloe_clean:
	rm -rf modelsim.ini
	rm -rf vsim.wlf
	rm -rf sim_build
	rm -rf transcript
	rm -rf results.xml
	rm -rf pycache
