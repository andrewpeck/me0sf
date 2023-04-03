test: test_fw test_sw

test_fw:
	python road/tb/test_pat_unit.py
	python road/tb/test_pat_unit_mux.py
	python road/tb/test_partition.py
	python road/tb/test_mult.py
	python road/tb/test_dav_to_phase.py
	python road/tb/test_fit.py
	python road/tb/test_chamber.py

test_sw:
	pytest road/tb/*_beh.py

types:
	python yml2hdl/yml2hdl.py -f road/hdl/pat_types.yml
