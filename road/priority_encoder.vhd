--TODO: need to simulate this

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.priority_encoder_pkg.all;

entity priority_encoder is
  generic(
    g_STAGE      : integer := 0;
    g_REG_INPUT  : boolean := false;
    g_REG_STAGES : integer := 2;
    g_DAT_SIZE   : integer := 1;
    g_QLT_SIZE   : integer := 1;
    g_WIDTH_i    : integer := 16;
    g_WIDTH_o    : integer := 1;
    g_ADR_SIZE_i : integer := 0;
    g_ADR_SIZE_o : integer := 5
    );
  port(
    --latch_i   : in  std_logic_vector (to g_WIDTH_i-1);
    clock : in std_logic;

    -- inputs
    dat_i : in bus_array (0 to g_WIDTH_i-1)(g_DAT_SIZE -1 downto 0);
    qlt_i : in bus_array (0 to g_WIDTH_i-1)(g_QLT_SIZE -1 downto 0);
    adr_i : in bus_array (0 to g_WIDTH_i-1)(g_ADR_SIZE_i-1 downto 0);

    -- outputs
    dat_o : out bus_array (0 to g_WIDTH_o-1)(g_DAT_SIZE -1 downto 0);
    qlt_o : out bus_array (0 to g_WIDTH_o-1)(g_QLT_SIZE -1 downto 0);
    adr_o : out bus_array (0 to g_WIDTH_o-1)(g_ADR_SIZE_o-1 downto 0)
    );
end priority_encoder;

architecture behavioral of priority_encoder is

  procedure best_1of2 (
    signal best_qlt, best_adr, best_dat: out std_logic_vector;
    qlt0, qlt1, adr0, adr1, dat0, dat1 : in std_logic_vector
    ) is
  begin
    if (qlt1 > qlt0) then
      best_adr <= ('1' & adr1);
      best_qlt <= qlt1;
      best_dat <= dat1;
    else
      best_adr <= ('0' & adr0);
      best_qlt <= qlt0;
      best_dat <= dat0;
    end if;
  end best_1of2;

  -- function width_of_stage (stage : integer; width : integer)
  --   return integer is
  --   variable width_buf  : integer;
  --   variable this_stage : integer;
  -- begin
  --   width_buf  := width;
  --   this_stage := 0;

  --   while (true) loop

  --     if (this_stage = stage) then
  --       return width_buf;
  --     end if;

  --     if (width_buf = 3) then
  --       return 3;
  --     end if;

  --     if (width_buf = 1) then
  --       return 1;
  --     end if;

  --     if (width_buf mod 2 /= 0) then
  --       width_buf := width_buf + 1;
  --     end if;

  --     width_buf := width_buf/2;

  --     this_stage := this_stage + 1;

  --   end loop;
  -- end function;

  -- function count_num_stages (width : integer)
  --   return integer is
  --   variable width_buf : integer;
  --   variable stage     : integer;
  -- begin
  --   width_buf := width;
  --   stage     := 0;

  --   while (true) loop
  --     if (width_buf = 3) then
  --       stage := stage + 1;
  --       return stage;
  --     end if;

  --     if (width_buf = 1) then
  --       return stage;
  --     end if;

  --     if (width_buf mod 2 /= 0) then
  --       width_buf := width_buf + 1;
  --     end if;

  --     width_buf := width_buf/2;

  --     stage := stage + 1;
  --   end loop;
  -- end function;

  function next_width (width : integer)
    return integer is
  begin
    -- for size=4 we reduce to 2 and add 1 bit
    -- for size=3 we reduce to 1 and add 2 bits
    -- for size=2 we reduce to 1 and add 1 bit
    if (width = 1) then
      return 1;
    elsif (width = 3) then
      return 1;
    elsif (width mod 2 = 0) then
      return width / 2;
    else
      return (width+1)/ 2;
    end if;
  end function;

  --function next_adr_size (size : integer; width : integer)
  --  return integer is
  --begin
  --  -- 5 and 6 we handle as special cases..
  --  -- for size=5 we reduce to 2 and add 1 bit
  --  if (width = 5 or width = 6) then    -- special cases add 2
  --    return size+2;
  --  else
  --    return size+1;                    -- usually just add 1
  --  end if;
  --end function;

	--function registered(signal Clock : std_logic; constant IsRegistered : boolean) return boolean is
	--begin
	--	if IsRegistered then
  --    return rising_edge(Clock);
	--	else
	--		return TRUE;
	--	end if;
	--end function;

begin

  assert false report "Generating priority encoder" severity note;

  -- do a 2:1 reduction of all of the inputs to form a 1/2 width comparison array
  -- feed this recursively into another encoder which will have 1 additional addrb
  comp_gen : if (g_WIDTH_i > 3) generate
    constant comp_out_width : integer := next_width(g_WIDTH_i);
    signal dat              : bus_array (0 to comp_out_width-1)(g_DAT_SIZE-1 downto 0);
    signal qlt              : bus_array (0 to comp_out_width-1)(g_QLT_SIZE-1 downto 0);
    signal adr              : bus_array (0 to comp_out_width-1)(g_ADR_SIZE_i downto 0);  -- add 1 bit
  begin

    assert false report " > Generating comparators for #inputs=" & integer'image(g_WIDTH_i) severity note;

    comp_loop : for icomp in 0 to comp_out_width-1 generate
    begin

      -- even cases are simple
      gen_even : if (icomp < comp_out_width -1 or (g_WIDTH_i mod 2 = 0)) generate
        assert false report "   > icomp: #" & integer'image(icomp+1) & " of " & integer'image(comp_out_width) & " compare: " & integer'image(icomp*2+1) & " to " & integer'image(icomp*2) severity note;
        process (clock) is
        begin
          if (rising_edge(clock) or
              (g_STAGE=0 and g_REG_INPUT) or
              (g_STAGE/=0 and (g_STAGE mod g_REG_STAGES=0))) then
            best_1of2 (qlt(icomp), adr(icomp), dat(icomp),
                       qlt_i(icomp*2), qlt_i(icomp*2+1),
                       adr_i(icomp*2), adr_i(icomp*2+1),
                       dat_i(icomp*2), dat_i(icomp*2+1));
          end if;
        end process;
      end generate;

      -- if we have an odd number of inputs, just choose highest # real entry (no comparator)
      gen_odd : if (g_WIDTH_i mod 2 /= 0 and icomp = comp_out_width-1) generate
        process (clock) is
        begin
          if (rising_edge(clock) or
              (g_STAGE=0 and g_REG_INPUT) or
              (g_STAGE/=0 and (g_STAGE mod g_REG_STAGES=0))) then
            assert false report "  > odd nocompare on : " & integer'image(icomp*2) severity note;
            dat(icomp) <= dat_i(icomp*2);
            qlt(icomp) <= qlt_i(icomp*2);
            adr(icomp) <= '0' & adr_i(icomp*2);
          end if;
        end process;
      end generate;

    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        g_STAGE      => g_STAGE + 1,
        g_REG_STAGES => g_REG_STAGES,
        g_WIDTH_i    => comp_out_width,
        g_WIDTH_o    => 1,
        g_DAT_SIZE   => g_DAT_SIZE,
        g_QLT_SIZE   => g_QLT_SIZE,
        g_ADR_SIZE_i => g_ADR_SIZE_i+1,  -- add 1 to next stage input
        g_ADR_SIZE_o => g_ADR_SIZE_o     -- add 1 or 3 to next output
        )
      port map (
        clock => clock,
        dat_i => dat,
        qlt_i => qlt,
        adr_i => adr,
        dat_o => dat_o,
        qlt_o => qlt_o,
        adr_o => adr_o
        );

  end generate;

  --------------------------------------------------------------------------------
  -- handle the final special cases
  --------------------------------------------------------------------------------

  -- for a single final case, just output it
  g_WIDTH1_gen : if (g_WIDTH_i = 1) generate
    qlt_o(0) <= qlt_i(0);
    adr_o(0) <= adr_i(0);
    dat_o(0) <= dat_i(0);
  end generate;

  -- for a double final case, choose 1 of 2
  g_WIDTH2_gen : if (g_WIDTH_i = 2) generate
    assert false report "   > 2:1 mux" severity note;
    process (clock) is
    begin
      if (rising_edge(clock)) then
        best_1of2 (qlt_o(0), adr_o(0), dat_o(0),
                   qlt_i(0), qlt_i(1),
                   adr_i(0), adr_i(1),
                   dat_i(0), dat_i(1));
      end if;
    end process;
  end generate;

  -- for a triple final case, choose 1 of 3
  g_WIDTH3_gen : if (g_WIDTH_i = 3) generate
    assert false report "   > 3:1 mux" severity note;
    process (clock) is
    begin
      if (rising_edge(clock)) then
        -- choose 2
        if (qlt_i(2) > qlt_i (1) and qlt_i(2) > qlt_i (0)) then
          qlt_o(0) <= qlt_i (2);
          adr_o(0) <= "10" & adr_i (2);
          dat_o(0) <= dat_i (2);
        -- choose 1
        elsif (qlt_i(1) > qlt_i (0)) then
          qlt_o(0) <= qlt_i (1);
          adr_o(0) <= "01" & adr_i (1);
          dat_o(0) <= dat_i (1);
        else
          qlt_o(0) <= qlt_i (0);
          adr_o(0) <= "00" & adr_i (0);
          dat_o(0) <= dat_i (0);
        end if;
      end if;
    end process;

  end generate;

end behavioral;
