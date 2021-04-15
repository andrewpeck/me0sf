.PHONY : build poc road

QUESTA =

ifdef QUESTA
ANALYZE=vcom -O5 -2008 -check_synthesis
ELABORATE=echo
RUN=vsim -batch -do "set NumericStdNoWarnings 1; run 500000; quit -f"
ifdef GUI
RUN_GUI = vsim -do "set NumericStdNoWarnings 1; do wave.do;"
else
RUN_GUI = $(RUN)
endif
#TAIL=
else
ANALYZE=ghdl -a --std=08 --ieee=synopsys -Wunused --warn-runtime-error --warn-body --warn-parenthesis --warn-reserved
ELABORATE=ghdl -e --std=08 --ieee=synopsys
RUN=ghdl -r --std=08 --ieee=synopsys
RUN_GUI = $(RUN)
RUNTAIL=--ieee-asserts=disable
RUNTAIL_GUI =$(RUNTAIL) --stop-time=5000ns --wave=chamber_tb.ghw
endif

build: chamber_tb

BITONIC_SRCS = 	hdl/bitonic_sort/poc_bitonic_sort_pkg.vhd \
		 						hdl/bitonic_sort/poc_bitonic_sort.vhd \
	  						hdl/bitonic_sort/bitonic_sort.vhd

PRIORITY_SRCS  = hdl/priority_encoder/hdl/priority_encoder.vhd \
									hdl/priority_encoder/tb/priority_encoder_inst.vhd

PATTERN_SRCS = $(PRIORITY_SRCS) hdl/pat_pkg.vhd  hdl/patterns.vhd hdl/pat_unit.vhd

PARTITION_SRCS = $(BITONIC_SRCS) \
									$(PATTERN_SRCS) \
									hdl/dav_to_phase.vhd \
									hdl/pat_unit_mux.vhd \
									hdl/ghost_cancellation.vhd \
									hdl/segment_selector.vhd \
									hdl/partition.vhd

CHAMBER_SRCS =  $(PARTITION_SRCS) hdl/chamber.vhd

sorter: $(BITONIC_SRCS)
	@$(ANALYZE) $(BITONIC_SRCS)
	$(RUN) bitonic_sort $(RUNTAIL)

priority: $(PRIORITY_SRCS)
	@$(ANALYZE) $(PRIORITY_SRCS)
	@$(RUN) priority_encoder_inst

patterns: $(PATTERN_SRCS)
	$(ANALYZE) $(PATTERN_SRCS)
	$(RUN) pat_unit $(RUNTAIL)

partition: $(PARTITION_SRCS)
	@$(ANALYZE) $(PARTITION_SRCS)

	$(RUN) segment_selector $(RUNTAIL)
	$(RUN) pat_unit_mux $(RUNTAIL)
	$(RUN) partition $(RUNTAIL)

chamber:  $(CHAMBER_SRCS)
	$(ANALYZE) $(CHAMBER_SRCS)
	$(RUN) chamber $(RUNTAIL)

chamber_tb: $(CHAMBER_SRCS) tb/chamber_tb.vhd
	@$(ANALYZE)   $(CHAMBER_SRCS) tb/chamber_tb.vhd
	$(RUN_GUI)    chamber_tb $(RUNTAIL)

run:
	@$(ANALYZE)   tb/chamber_tb.vhd
	$(RUN_GUI)    chamber_tb $(RUNTAIL_GUI)


vivado:
	vivado -mode batch -notrace -source build.tcl | ccze -A

clean:
	rm -f *.o *.cf
	rm -f partition
	rm -f pat_unit
	rm -f chamber
	rm -rf work

rust_hdl:
	vhdl_lang  -c ../vhdl_ls.toml
