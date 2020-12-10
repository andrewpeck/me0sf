.PHONY : build poc road

#ANALYZE_CMD=vcom -2008 -check_synthesis
ANALYZE=ghdl -a --std=08 --ieee=synopsys
ELABORATE=ghdl -e --std=08 --ieee=synopsys
build: poc road prbs

poc:
#@ghdl  -a --std=08 --work=PoC --ieee=synopsys
	$(ANALYZE) --work=PoC \
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
	$(ANALYZE) pat_pkg.vhd  patterns.vhd priority_encoder/priority_encoder_pkg.vhd priority_encoder/priority_encoder.vhd
	$(ANALYZE) pat_unit.vhd
	$(ELABORATE) pat_unit
	./pat_unit

road: patterns poc
	$(ANALYZE) ghost_cancellation.vhd segment_selector.vhd partition.vhd chamber.vhd
	$(ELABORATE) partition
	$(ELABORATE) chamber

prbs: road
	$(ANALYZE) prbs31.vhd
	$(ANALYZE) chamber_prbs.vhd
	$(ELABORATE) chamber_prbs

run: prbs
	./chamber_prbs --ieee-asserts=disable

clean:
	rm -f *.o *.cf
	rm -f partition
	rm -f pat_unit
	rm -f chamber
