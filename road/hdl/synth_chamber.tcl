read_vhdl -vhdl2008 -library work {
    priority_encoder/hdl/priority_encoder.vhd
    pat_types.vhd
    pat_pkg.vhd
    bitonic_sort/poc_bitonic_sort_pkg.vhd
    bitonic_sort/poc_bitonic_sort.vhd
    bitonic_sort/kawazome/bitonic_exchange.vhd
    bitonic_sort/kawazome/bitonic_merge.vhd
    bitonic_sort/kawazome/bitonic_sorter.vhd
    bitonic_sort/bitonic_sort.vhd
    patterns.vhd
    hit_count.vhd
    segment_selector.vhd
    pat_unit.vhd
    fixed_delay.vhd
    dav_to_phase.vhd
    pat_unit_mux.vhd
    deghost.vhd
    partition.vhd
    pulse_extension.vhd
    chamber_pulse_extension.vhd
    chamber.vhd}

synth_design -top chamber -part xcku15p-ffva1760-2-e
report_utilization -file chamber_utilization.txt
