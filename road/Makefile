.PHONY : build poc road

#ANALYZE=vcom -2008 -check_synthesis
ANALYZE=ghdl -a --std=08 --ieee=synopsys
ELABORATE=ghdl -e --std=08 --ieee=synopsys
RUN=ghdl -r --std=08 --ieee=synopsys
build: poc road prbs

BITONIC_SRCS = 	hdl/bitonic_sort/poc_bitonic_sort_pkg.vhd \
		 						hdl/bitonic_sort/poc_bitonic_sort.vhd \
	  						hdl/bitonic_sort/bitonic_sort.vhd

poc: $(BITONIC_SRCS)
	$(ANALYZE) $(BITONIC_SRCS)

patterns:
	$(ANALYZE)   hdl/pat_pkg.vhd  hdl/patterns.vhd hdl/priority_encoder/hdl/priority_encoder.vhd
	$(ANALYZE)   hdl/pat_unit.vhd
	$(ELABORATE) pat_unit
	$(RUN)       pat_unit

road: patterns poc
	$(ANALYZE)   ghost_cancellation.vhd segment_selector.vhd partition.vhd chamber.vhd
	$(ELABORATE) partition
	$(ELABORATE) chamber

prbs: road
	$(ANALYZE)   prbs31.vhd
	$(ANALYZE)   chamber_prbs.vhd
	$(ELABORATE) chamber_prbs

run: prbs
	./chamber_prbs --ieee-asserts=disable

clean:
	rm -f *.o *.cf
	rm -f partition
	rm -f pat_unit
	rm -f chamber

rust_hdl:
	vhdl_lang  -c ../vhdl_ls.toml
