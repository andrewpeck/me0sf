# generates the look up table for our linear regression software
from subfunc import *

def generate_vhdl_lines(centroids):
    """convert final centroid, data, and width pairings into vhdl lines to write to find_centoid.vhd file"""
    lines = []

    for centroid_group in centroids:

        length = centroid_group[0]
        data = centroid_group[1]

        lines.append("  if (length = %d) then" % length)
        lines.append("    case ly%s is" % ("(0)" if length == 1 else ""))
        sep =  "\'" if length==1 else "\""

        for centroid in data:
            value = centroid[0]
            centroid = centroid[1]
            lines.append(f"     when {sep}%s{sep} => index := %d;" % (bin(value)[2:].zfill(length), centroid))

        lines.append("     when others => index := 0;")
        lines.append("    end case;")
        lines.append("  end if;")
        lines.append("\n")

    return lines

if __name__ == "__main__":

    centroids = get_centroids(14)

    print(centroids)

    vhdl_lines = generate_vhdl_lines(centroids)

    # remember this lut is arranged every combo of each width from [1,3,4,5,6,8,9,12,14]
    # write stored vhdl lines into the find_centoid.vhd file; use same format as the find_centoid function in the me0sf repository
    start = [

        "library ieee;",
        "use ieee.std_logic_1164.all;",
        "use ieee.std_logic_misc.all;",
        "use ieee.numeric_std.all;\n",
        "package centroid_finding is",
        "  function centroid (ly : std_logic_vector; length : natural) return natural ;",
        "end package centroid_finding;\n",
        "package body centroid_finding is\n",
        "  function centroid (ly : std_logic_vector; length : natural) return natural is",
        "    variable index : natural;\n",
        "  begin\n",
    ]

    f = open("../hdl/centroid_finding.vhd", "w")

    for i in range(len(start)):
        f.write(start[i])
        f.write("\n")

    for j in range(len(vhdl_lines)):
        f.write(vhdl_lines[j])
        f.write("\n")

    f.write("  return index;\n\n")
    f.write("  end function;\n\n")
    f.write("end package body;\n")
    f.close()
