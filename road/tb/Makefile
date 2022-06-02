test:
	TOPLEVEL_LANG=vhdl SIM=questa pytest -n 4 -v

fit:
	cp sim_build/wave.do test_fit_wave.do
	make clean
	mkdir sim_build
	cp test_fit_wave.do sim_build/wave.do
	SIM=questa python test_fit.py 2>&1  | ccze -A

clean:
	@rm -rf __pycache__ sim_build

#build:
#	 vcom -mixedsvvh -work priority_encoder_inst -2008 /home/andrew/Dropbox/me0sf/road/priority_encoder/hdl/priority_encoder.vhd /home/andrew/Dropbox/me0sf/road/priority_encoder/tb/priority_encoder_inst.vhd
