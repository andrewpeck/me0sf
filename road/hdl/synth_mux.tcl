read_vhdl -vhdl2008 -library work {
    pat_types.vhd
    pat_pkg.vhd
    mux_single.vhd
    mux_partition.vhd
    mux_chamber.vhd
    fixed_delay.vhd
    dav_to_phase.vhd
    mux_chamber_multi.vhd
}

synth_design -top mux_chamber_multi -part xcku15p-ffva1760-2-e

report_utilization -file "mux_utilization.txt"
