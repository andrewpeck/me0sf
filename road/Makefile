.PHONY : build poc road

#all: run_tdc_decoder
#
#run_tdc_decoder: tdc_decoder_tb
#	@./tdc_decoder_tb


build: poc road

poc:
#@ghdl  -a --std=08 --work=PoC --ieee=synopsys
	@ghdl  -a --std=08 --work=PoC --ieee=synopsys \
			poc/poc*.vhdl \
			../PoC/src/common/utils.vhdl \
			../PoC/src/common/config.vhdl \
			../PoC/src/common/strings.vhdl \
			../PoC/src/common/debug.vhdl \
			../PoC/src/common/protected.v08.vhdl \
			../PoC/src/common/fileio.v08.vhdl \
			../PoC/src/common/math.vhdl \
			../PoC/src/common/physical.vhdl \
			../PoC/src/common/vectors.vhdl \
			../PoC/src/common/common.vhdl \
			../PoC/src/common/components.vhdl \
			../PoC/src/sort/sortnet/sortnet_BitonicSort.vhdl

patterns:
	@ghdl -a --std=08 --ieee=synopsys pat_pkg.vhd  patterns.vhd \
														priority_encoder/priority_encoder_pkg.vhd priority_encoder/priority_encoder.vhd \
														pat_unit.vhd
	@ghdl -e --std=08 --ieee=synopsys pat_unit
	./pat_unit

road: patterns poc
	@ghdl -a --std=08 --ieee=synopsys ghost_cancellation.vhd segment_selector.vhd partition.vhd chamber.vhd \
	@ghdl -e --std=08 --ieee=synopsys partition
	@ghdl -e --std=08 --ieee=synopsys chamber

clean:
	rm -f *.o *.cf
