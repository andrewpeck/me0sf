.PHONY : build poc road

QUESTA =

ifdef QUESTA
ANALYZE=vcom -2008 -check_synthesis
ELABORATE=echo
RUN=vsim -batch -do "set NumericStdNoWarnings 1; run 10000; quit -f"
ifdef GUI
RUN_GUI = vsim -debugDB
else
RUN_GUI = $(RUN)
endif
#TAIL=
else
ANALYZE=ghdl -a --std=08 --ieee=synopsys -Wunused --warn-runtime-error --warn-body --warn-parenthesis --warn-reserved
ELABORATE=ghdl -e --std=08 --ieee=synopsys
RUN=ghdl -r --std=08 --ieee=synopsys
RUNTAIL=--ieee-asserts=disable
endif

build: chamber_tb

BITONIC_SRCS = 	hdl/bitonic_sort/poc_bitonic_sort_pkg.vhd \
		 						hdl/bitonic_sort/poc_bitonic_sort.vhd \
	  						hdl/bitonic_sort/bitonic_sort.vhd

sorter: $(BITONIC_SRCS)
	@$(ANALYZE) $(BITONIC_SRCS)
	$(RUN) bitonic_sort $(RUNTAIL)

priority:
	@$(ANALYZE) hdl/priority_encoder/hdl/priority_encoder.vhd

patterns: priority
	@$(ANALYZE)   hdl/pat_pkg.vhd  hdl/patterns.vhd
	@$(ANALYZE)   hdl/pat_unit.vhd

	$(RUN)       pat_unit $(RUNTAIL)

partition: patterns sorter
	@$(ANALYZE) hdl/dav_to_phase.vhd hdl/pat_unit_mux.vhd hdl/ghost_cancellation.vhd hdl/segment_selector.vhd hdl/partition.vhd

	$(RUN) segment_selector $(RUNTAIL)
	$(RUN) pat_unit_mux $(RUNTAIL)
	$(RUN) partition $(RUNTAIL)

chamber: patterns sorter partition
	@$(ANALYZE) hdl/chamber.vhd
	$(RUN) chamber $(RUNTAIL)

chamber_tb: chamber
	@$(ANALYZE)   tb/chamber_tb.vhd
	$(RUN_GUI)    chamber_tb $(RUNTAIL)

run:
	@$(ANALYZE)   tb/chamber_tb.vhd
	$(RUN_GUI)    chamber_tb $(RUNTAIL)


vivado:
	vivado -mode batch -notrace -source build.tcl | ccze -A

#run: prbs
#	./chamber_prbs --ieee-asserts=disable

clean:
	rm -f *.o *.cf
	rm -f partition
	rm -f pat_unit
	rm -f chamber
	rm -rf work

rust_hdl:
	vhdl_lang  -c ../vhdl_ls.toml
