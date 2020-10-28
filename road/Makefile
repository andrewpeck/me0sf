.PHONY : build

#all: run_tdc_decoder
#
#run_tdc_decoder: tdc_decoder_tb
#	@./tdc_decoder_tb

build:
	@ghdl  -a --std=08 --ieee=synopsys pat_pkg.vhd  patterns.vhd pat_unit.vhd sf_pkg.vhd partition.vhd
	@ghdl -e --std=08 --ieee=synopsys partition

clean:
	rm *.o *.cf
