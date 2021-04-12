.PHONY : build poc road

GHDL = true

ifdef $(GHDL)
ANALYZE=ghdl -a --std=08 --ieee=synopsys
ELABORATE=ghdl -e --std=08 --ieee=synopsys
RUN=ghdl -r --std=08 --ieee=synopsys
endif

#ifdef $(QUESTA)
ANALYZE=vcom -2008 -check_synthesis
ELABORATE=echo
RUN=vsim
TAIL=log -r * run 100000000 quit -f
#endif

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
	$(RUN)       pat_unit $(TAIL)

road: patterns poc
	$(ANALYZE)   hdl/dav_to_phase.vhd hdl/pat_unit_mux.vhd hdl/ghost_cancellation.vhd hdl/segment_selector.vhd hdl/partition.vhd hdl/chamber.vhd
	$(ELABORATE) partition
	$(ELABORATE) chamber

prbs: road
	$(ANALYZE)   tb/prbs31.vhd
	$(ANALYZE)   tb/chamber_prbs.vhd
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
