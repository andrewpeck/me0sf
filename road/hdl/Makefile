synth_pat_unit:
	vivado -mode batch -source synth_pat_unit.tcl -notrace
	make clean

synth_chamber:
	vivado -mode batch -source synth_chamber.tcl -notrace
	make clean

clean:
	rm vivado*.jou
	rm vivado*.log
