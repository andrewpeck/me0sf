# generates the look up table for our linear regression software
from subfunc import *

def generate_vhdl_lines(centroids):
    """convert final centroid, data, and width pairings into vhdl lines to write to find_centoid.vhd file"""
    lines = []

    for centroid_group in centroids:

        length = centroid_group[0]
        data = centroid_group[1]

        lines.append("  gen_%d : if (length = %d) generate" % (length,length))
        #lines.append("    signal index : natural;")
        lines.append("  begin")
        lines.append("    process (clk) is")
        lines.append("    begin")
        lines.append("      if (rising_edge(clk)) then")
        lines.append("        case din%s is" % ("(0)" if length == 1 else ""))
        sep =  "\'" if length==1 else "\""

        for centroid in data:
            value = centroid[0]
            centroid = centroid[1]
            lines.append(f"         when {sep}%s{sep} => index <= %d;" % (bin(value)[2:].zfill(length), centroid))

        lines.append("         when others => index <= 0;")
        lines.append("        end case;")
        lines.append("      end if;")
        lines.append("    end process;")
        lines.append("  dout <= to_unsigned(index, NBITS);")
        lines.append("  end generate;")
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
        "\n",
        "entity centroid_finder is\n",
        "  generic(LENGTH : integer; NBITS : integer);\n",
        "  port(\n",
        "    clk : in std_logic;\n",
        "    din : in std_logic_vector(LENGTH-1 downto 0);\n",
        "    dout : out unsigned(NBITS-1 downto 0)\n",
        "    );\n",
        "end centroid_finder;\n",
        "\n",
        "architecture behavioral of centroid_finder is\n",
        "    signal index : natural range 0 to LENGTH;\n",
        "\n",
        "begin\n",
    ]

    f = open("../hdl/centroid_finder.vhd", "w")

    for i in range(len(start)):
        f.write(start[i])
        f.write("\n")

    for j in range(len(vhdl_lines)):
        f.write(vhdl_lines[j])
        f.write("\n")

    f.write("\n")
    f.write("\n")
    f.write("end behavioral;\n")
    f.close()
