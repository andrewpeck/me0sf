set UTIL_MAX 359

read_vhdl -vhdl2008 -library work {
    pat_types.vhd
    pat_pkg.vhd
    patterns.vhd
    hit_count.vhd
    priority_encoder/hdl/priority_encoder.vhd
    pat_unit.vhd}

synth_design -top pat_unit -part xc7a12tcpg238-3

report_utilization -file "pat_unit_utilization.txt"

# write_sdf -force pat_unit.sdf
# write_verilog -force -cell pat_unit -mode timesim -sdf_anno true -sdf_file ../../hdl/pat_unit.sdf pat_unit_timing.v

exec cat pat_unit_utilization.txt

set util [exec awk {-F\\|} {/Slice LUTs*/{print int($3)}} pat_unit_utilization.txt]

puts "Pat Unit Utilization: $util LUTs."

if {$util > $UTIL_MAX} {
    error "Utilization is greater than imposed max=$UTIL_MAX. If
an increase in utilization is expected, then edit hdl/synth_pat_unit.tcl to
change the limit. This warning is here to avoid unanticipated increases."
}

if {$util < $UTIL_MAX} {
    error "Congratulations on improving the pat_unit utilization to $util. You should update
the max limit in hdl/synth_pat_unit.tcl to make sure there are no regressions in the future."
}
