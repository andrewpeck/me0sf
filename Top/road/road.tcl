#vivado
############# modify these to match project ################
set BIN_FILE 0
set USE_QUESTA_SIMULATOR 0

#source ./fpga.tcl
set FPGA xcvu13p-flga2577-1-e
#set FPGA xc7a200tfbg484-3

set SIMULATOR  xsim

## FPGA and Vivado strategies and flows
regexp -- {Vivado v([0-9]{4})\.[0-9]} [version] -> VIVADO_YEAR
set SYNTH_STRATEGY "Vivado Synthesis Defaults"
set SYNTH_FLOW "Vivado Synthesis $VIVADO_YEAR"
set IMPL_STRATEGY "Vivado Implementation Defaults"
set IMPL_FLOW "Vivado Implementation $VIVADO_YEAR"

### Set Vivado Runs Properties ###
#
# ATTENTION: The \ character must be the last one of each line
#
# The default Vivado run names are: synth_1 for synthesis and impl_1 for implementation.
#
# To find out the exact name and value of the property, use Vivado GUI to click on the checkbox you like.
# This will make Vivado run the set_property command in the Tcl console.
# Then copy and paste the name and the values from the Vivado Tcl console into the lines below.

set PROPERTIES [dict create \
synth_1 [dict create \
    STEPS.SYNTH_DESIGN.ARGS.ASSERT true \
    STEPS.SYNTH_DESIGN.ARGS.KEEP_EQUIVALENT_REGISTERS true \
    STEPS.SYNTH_DESIGN.ARGS.RETIMING false \
  ] \
impl_1 [dict create \
  STEPS.OPT_DESIGN.ARGS.DIRECTIVE Default \
  STEPS.POST_ROUTE_PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore \
  ]\
]

############################################################

set DESIGN    "[file rootname [file tail [info script]]]"
set PATH_REPO "[file normalize [file dirname [info script]]]/../../"

set_property top chamber [current_fileset]
source $PATH_REPO/Hog/Tcl/create_project.tcl
