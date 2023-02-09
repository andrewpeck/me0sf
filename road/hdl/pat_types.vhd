-- This file was auto-generated by YML2HDL tool.
-- https://gitlab.com/tcpaiva/yml2hdl
-- 2023-02-09 14:34:25

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

package pat_types is

   -- yml2hdl types --

   type std_logic_vector_array is array(integer range <>) of std_logic_vector;

   -- yml2hdl attributes --

   attribute w : natural;

   -- Basic converting functions --

   procedure assign(
      variable y : out std_logic_vector;
      constant x : in std_logic_vector);

   function convert(x: std_logic_vector; t: std_logic_vector) return std_logic_vector;

   function width(x: std_logic) return natural;
   function width(x: std_logic_vector) return natural;
   function width(x: unsigned) return natural;
   function width(x: signed) return natural;
   function width(x: integer) return natural;

   function convert(x: std_logic_vector; t: signed) return signed;
   function convert(x: std_logic_vector; t: unsigned) return unsigned;
   function convert(x: std_logic_vector; t: integer) return integer;
   function convert(x: std_logic_vector; t: std_logic) return std_logic;

   function convert(x: signed; t: std_logic_vector) return std_logic_vector;
   function convert(x: unsigned; t: std_logic_vector) return std_logic_vector;
   function convert(x: integer; t: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic; t: std_logic_vector) return std_logic_vector;

   function zero(y: std_logic) return std_logic;
   function zero(y: std_logic_vector) return std_logic_vector;
   function zero(y: unsigned) return unsigned;
   function zero(y: signed) return signed;
   function zero(y: integer) return integer;

   -- Custom types and functions --

   -- CNT_BITS: number of bits to count all hits in 6 layers
   constant CNT_BITS : integer := 5;
   attribute w of CNT_BITS : constant is 32;

   -- PID_BITS: number of bits to cnt the pids
   constant PID_BITS : integer := 4;
   attribute w of PID_BITS : constant is 32;

   -- CENTROID_BITS: number of bits to cnt the centroid
   constant CENTROID_BITS : integer := 4;
   attribute w of CENTROID_BITS : constant is 32;

   -- STRIP_BITS: 8 bits to count 0-191
   constant STRIP_BITS : integer := 8;
   attribute w of STRIP_BITS : constant is 32;

   constant PATTERN_SORTB : integer := 17; -- CNT_BITS+PID_BITS+STRIP_BITS
   attribute w of PATTERN_SORTB : constant is 32;

   -- PARTITION_BITS: 3 bits to count 0-7
   constant PARTITION_BITS : integer := 3;
   attribute w of PARTITION_BITS : constant is 32;

   type hi_lo_t is record
      hi : integer;
      lo : integer;
   end record hi_lo_t;
   attribute w of hi_lo_t : type is 64;
   function width(x: hi_lo_t) return natural;
   function convert(x: hi_lo_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: hi_lo_t) return hi_lo_t;
   function zero(tpl: hi_lo_t) return hi_lo_t;

   type patdef_t is record
      id : natural;
      ly0 : hi_lo_t;
      ly1 : hi_lo_t;
      ly2 : hi_lo_t;
      ly3 : hi_lo_t;
      ly4 : hi_lo_t;
      ly5 : hi_lo_t;
   end record patdef_t;
   attribute w of patdef_t : type is 416;
   function width(x: patdef_t) return natural;
   function convert(x: patdef_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: patdef_t) return patdef_t;
   function zero(tpl: patdef_t) return patdef_t;

   type centroid_array_t is array(0 to 5) of unsigned(CENTROID_BITS-1 downto 0);
   attribute w of centroid_array_t : type is 24;
   function width(x: centroid_array_t) return integer;
   function convert(x: centroid_array_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: centroid_array_t) return centroid_array_t;
   function zero(tpl: centroid_array_t) return centroid_array_t;
   function convert(x: centroid_array_t; tpl: std_logic_vector_array) return std_logic_vector_array;
   function convert(x: std_logic_vector_array; tpl: centroid_array_t) return centroid_array_t;

   subtype layer_t is std_logic_vector(191 downto 0);
   attribute w of layer_t : subtype is 192;

   type partition_t is array(0 to 5) of layer_t;
   attribute w of partition_t : type is 1152;
   function width(x: partition_t) return integer;
   function convert(x: partition_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: partition_t) return partition_t;
   function zero(tpl: partition_t) return partition_t;
   function convert(x: partition_t; tpl: std_logic_vector_array) return std_logic_vector_array;
   function convert(x: std_logic_vector_array; tpl: partition_t) return partition_t;

   type int_array_t is array(integer range <>) of integer;
   function width(x: int_array_t) return integer;
   function convert(x: int_array_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: int_array_t) return int_array_t;
   function zero(tpl: int_array_t) return int_array_t;
   function convert(x: int_array_t; tpl: std_logic_vector_array) return std_logic_vector_array;
   function convert(x: std_logic_vector_array; tpl: int_array_t) return int_array_t;

   type patdef_array_t is array(integer range <>) of patdef_t;
   function width(x: patdef_array_t) return integer;
   function convert(x: patdef_array_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: patdef_array_t) return patdef_array_t;
   function zero(tpl: patdef_array_t) return patdef_array_t;
   function convert(x: patdef_array_t; tpl: std_logic_vector_array) return std_logic_vector_array;
   function convert(x: std_logic_vector_array; tpl: patdef_array_t) return patdef_array_t;

   type segment_t is record
      hits : centroid_array_t;
      partition : unsigned(2 downto 0);
      cnt : unsigned(CNT_BITS-1 downto 0);
      id : unsigned(PID_BITS-1 downto 0);
      strip : unsigned(7 downto 0);
   end record segment_t;
   attribute w of segment_t : type is 44;
   function width(x: segment_t) return natural;
   function convert(x: segment_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: segment_t) return segment_t;
   function zero(tpl: segment_t) return segment_t;

   type segment_list_t is array(integer range <>) of segment_t;
   function width(x: segment_list_t) return integer;
   function convert(x: segment_list_t; tpl: std_logic_vector) return std_logic_vector;
   function convert(x: std_logic_vector; tpl: segment_list_t) return segment_list_t;
   function zero(tpl: segment_list_t) return segment_list_t;
   function convert(x: segment_list_t; tpl: std_logic_vector_array) return std_logic_vector_array;
   function convert(x: std_logic_vector_array; tpl: segment_list_t) return segment_list_t;

end package pat_types;

------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

package body pat_types is

   -- Basic converting functions --

   procedure assign(
      variable y : out std_logic_vector;
      constant x : in std_logic_vector) is
      variable tmp : std_logic_vector(y'range);
   begin
      for j in 0 to y'length-1 loop
         y(y'low + j) := x(x'low + j);
      end loop;
   end procedure assign;

   function convert(x: std_logic_vector; t: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(t'range);
   begin
      assign(y, x);
      return y;
   end function convert;
   function width(x: std_logic) return natural is
   begin
      return 1;
   end function width;
   function width(x: std_logic_vector) return natural is
   begin
      return x'length;
   end function width;
   function width(x: unsigned) return natural is
   begin
      return x'length;
   end function width;
   function width(x: signed) return natural is
   begin
      return x'length;
   end function width;
   function width(x: integer) return natural is
   begin
      return 32;
   end function width;

   function convert(x: std_logic_vector; t: signed) return signed is
      variable y: signed(t'range);
   begin
      y := signed(x);
      return y;
   end function convert;
   function convert(x: std_logic_vector; t: unsigned) return unsigned is
      variable y: unsigned(t'range);
   begin
      y := unsigned(x);
      return y;
   end function convert;
   function convert(x: std_logic_vector; t: integer) return integer is
      variable y: integer;
   begin
      y := to_integer(signed(x));
      return y;
   end function convert;
   function convert(x: std_logic_vector; t: std_logic) return std_logic is
      variable y: std_logic;
   begin
      y := x(x'low);
      return y;
   end function convert;

   function convert(x: signed; t: std_logic_vector) return std_logic_vector is
   begin
      return std_logic_vector(x);
   end function convert;
   function convert(x: unsigned; t: std_logic_vector) return std_logic_vector is
   begin
      return std_logic_vector(x);
   end function convert;
   function convert(x: integer; t: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(t'range);
   begin
      assign(y, std_logic_vector(to_signed(x, 32)));
      return y;
   end function convert;
   function convert(x: std_logic; t: std_logic_vector) return std_logic_vector is
      variable y: std_logic_vector(t'range);
   begin
      y(y'low) := x;
      return y;
   end function convert;

   function zero(y: std_logic) return std_logic is
   begin
      return '0';
   end function zero;
   function zero(y: std_logic_vector) return std_logic_vector is
   begin
      return (y'range => '0');
   end function zero;
   function zero(y: unsigned) return unsigned is
   begin
      return to_unsigned(0, y'length);
   end function zero;
   function zero(y: signed) return signed is
   begin
      return to_signed(0, y'length);
   end function zero;
   function zero(y: integer) return integer is
   begin
      return 0;
   end function zero;

   -- Custom types and functions --

   function width(x: hi_lo_t) return natural is
      variable w : natural := 0;
   begin
      w := w + width(x.hi);
      w := w + width(x.lo);
      return w;
   end function width;
   function convert(x: hi_lo_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      variable w : integer;
      variable u : integer := tpl'left;
   begin
      if tpl'ascending then
         w := width(x.hi);
         y(u to u+w-1) := convert(x.hi, y(u to u+w-1));
         u := u + w;
         w := width(x.lo);
         y(u to u+w-1) := convert(x.lo, y(u to u+w-1));
      else
         w := width(x.hi);
         y(u downto u-w+1) := convert(x.hi, y(u downto u-w+1));
         u := u - w;
         w := width(x.lo);
         y(u downto u-w+1) := convert(x.lo, y(u downto u-w+1));
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: hi_lo_t) return hi_lo_t is
      variable y : hi_lo_t;
      variable w : integer;
      variable u : integer := x'left;
   begin
      if x'ascending then
         w := width(tpl.hi);
         y.hi := convert(x(u to u+w-1), tpl.hi);
         u := u + w;
         w := width(tpl.lo);
         y.lo := convert(x(u to u+w-1), tpl.lo);
      else
         w := width(tpl.hi);
         y.hi := convert(x(u downto u-w+1), tpl.hi);
         u := u - w;
         w := width(tpl.lo);
         y.lo := convert(x(u downto u-w+1), tpl.lo);
      end if;
      return y;
   end function convert;
   function zero(tpl: hi_lo_t) return hi_lo_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;

   function width(x: patdef_t) return natural is
      variable w : natural := 0;
   begin
      w := w + width(x.id);
      w := w + width(x.ly0);
      w := w + width(x.ly1);
      w := w + width(x.ly2);
      w := w + width(x.ly3);
      w := w + width(x.ly4);
      w := w + width(x.ly5);
      return w;
   end function width;
   function convert(x: patdef_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      variable w : integer;
      variable u : integer := tpl'left;
   begin
      if tpl'ascending then
         w := width(x.id);
         y(u to u+w-1) := convert(x.id, y(u to u+w-1));
         u := u + w;
         w := width(x.ly0);
         y(u to u+w-1) := convert(x.ly0, y(u to u+w-1));
         u := u + w;
         w := width(x.ly1);
         y(u to u+w-1) := convert(x.ly1, y(u to u+w-1));
         u := u + w;
         w := width(x.ly2);
         y(u to u+w-1) := convert(x.ly2, y(u to u+w-1));
         u := u + w;
         w := width(x.ly3);
         y(u to u+w-1) := convert(x.ly3, y(u to u+w-1));
         u := u + w;
         w := width(x.ly4);
         y(u to u+w-1) := convert(x.ly4, y(u to u+w-1));
         u := u + w;
         w := width(x.ly5);
         y(u to u+w-1) := convert(x.ly5, y(u to u+w-1));
      else
         w := width(x.id);
         y(u downto u-w+1) := convert(x.id, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly0);
         y(u downto u-w+1) := convert(x.ly0, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly1);
         y(u downto u-w+1) := convert(x.ly1, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly2);
         y(u downto u-w+1) := convert(x.ly2, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly3);
         y(u downto u-w+1) := convert(x.ly3, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly4);
         y(u downto u-w+1) := convert(x.ly4, y(u downto u-w+1));
         u := u - w;
         w := width(x.ly5);
         y(u downto u-w+1) := convert(x.ly5, y(u downto u-w+1));
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: patdef_t) return patdef_t is
      variable y : patdef_t;
      variable w : integer;
      variable u : integer := x'left;
   begin
      if x'ascending then
         w := width(tpl.id);
         y.id := convert(x(u to u+w-1), tpl.id);
         u := u + w;
         w := width(tpl.ly0);
         y.ly0 := convert(x(u to u+w-1), tpl.ly0);
         u := u + w;
         w := width(tpl.ly1);
         y.ly1 := convert(x(u to u+w-1), tpl.ly1);
         u := u + w;
         w := width(tpl.ly2);
         y.ly2 := convert(x(u to u+w-1), tpl.ly2);
         u := u + w;
         w := width(tpl.ly3);
         y.ly3 := convert(x(u to u+w-1), tpl.ly3);
         u := u + w;
         w := width(tpl.ly4);
         y.ly4 := convert(x(u to u+w-1), tpl.ly4);
         u := u + w;
         w := width(tpl.ly5);
         y.ly5 := convert(x(u to u+w-1), tpl.ly5);
      else
         w := width(tpl.id);
         y.id := convert(x(u downto u-w+1), tpl.id);
         u := u - w;
         w := width(tpl.ly0);
         y.ly0 := convert(x(u downto u-w+1), tpl.ly0);
         u := u - w;
         w := width(tpl.ly1);
         y.ly1 := convert(x(u downto u-w+1), tpl.ly1);
         u := u - w;
         w := width(tpl.ly2);
         y.ly2 := convert(x(u downto u-w+1), tpl.ly2);
         u := u - w;
         w := width(tpl.ly3);
         y.ly3 := convert(x(u downto u-w+1), tpl.ly3);
         u := u - w;
         w := width(tpl.ly4);
         y.ly4 := convert(x(u downto u-w+1), tpl.ly4);
         u := u - w;
         w := width(tpl.ly5);
         y.ly5 := convert(x(u downto u-w+1), tpl.ly5);
      end if;
      return y;
   end function convert;
   function zero(tpl: patdef_t) return patdef_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;

   function width(x: centroid_array_t) return integer is
      variable w : integer := x'length * width(x(x'low));
   begin
      return w;
   end function width;
   function convert(x: centroid_array_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      constant W : natural := width(x(x'low));
      variable a : integer;
      variable b : integer;
   begin
      if y'ascending then
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(b to a), convert(x(i+x'low), y(b to a)));
         end loop;
      else
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(a downto b), convert(x(i+x'low), y(a downto b)));
         end loop;
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: centroid_array_t) return centroid_array_t is
      variable y : centroid_array_t;
      constant W : natural := width(y(y'low));
      variable a : integer;
      variable b : integer;
   begin
      if x'ascending then
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(b to a), y(i+y'low));
         end loop;
      else
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(a downto b), y(i+y'low));
         end loop;
      end if;
      return y;
   end function convert;
   function zero(tpl: centroid_array_t) return centroid_array_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;
   function convert(x: centroid_array_t; tpl: std_logic_vector_array) return std_logic_vector_array is
      variable y : std_logic_vector_array(tpl'range)(tpl(tpl'low)'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), (y(j)'range => '0'));
      end loop;
      return y;
   end function convert;
   function convert(x: std_logic_vector_array; tpl: centroid_array_t) return centroid_array_t is
      variable y : centroid_array_t;
   begin
      for j in y'range loop
          y(j) := convert(x(j), y(j));
      end loop;
      return y;
   end function convert;

   function width(x: partition_t) return integer is
      variable w : integer := x'length * width(x(x'low));
   begin
      return w;
   end function width;
   function convert(x: partition_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      constant W : natural := width(x(x'low));
      variable a : integer;
      variable b : integer;
   begin
      if y'ascending then
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(b to a), convert(x(i+x'low), y(b to a)));
         end loop;
      else
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(a downto b), convert(x(i+x'low), y(a downto b)));
         end loop;
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: partition_t) return partition_t is
      variable y : partition_t;
      constant W : natural := width(y(y'low));
      variable a : integer;
      variable b : integer;
   begin
      if x'ascending then
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(b to a), y(i+y'low));
         end loop;
      else
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(a downto b), y(i+y'low));
         end loop;
      end if;
      return y;
   end function convert;
   function zero(tpl: partition_t) return partition_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;
   function convert(x: partition_t; tpl: std_logic_vector_array) return std_logic_vector_array is
      variable y : std_logic_vector_array(tpl'range)(tpl(tpl'low)'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), (y(j)'range => '0'));
      end loop;
      return y;
   end function convert;
   function convert(x: std_logic_vector_array; tpl: partition_t) return partition_t is
      variable y : partition_t;
   begin
      for j in y'range loop
          y(j) := convert(x(j), y(j));
      end loop;
      return y;
   end function convert;

   function width(x: int_array_t) return integer is
      variable w : integer := x'length * width(x(x'low));
   begin
      return w;
   end function width;
   function convert(x: int_array_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      constant W : natural := width(x(x'low));
      variable a : integer;
      variable b : integer;
   begin
      if y'ascending then
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(b to a), convert(x(i+x'low), y(b to a)));
         end loop;
      else
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(a downto b), convert(x(i+x'low), y(a downto b)));
         end loop;
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: int_array_t) return int_array_t is
      variable y : int_array_t(tpl'range);
      constant W : natural := width(y(y'low));
      variable a : integer;
      variable b : integer;
   begin
      if x'ascending then
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(b to a), y(i+y'low));
         end loop;
      else
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(a downto b), y(i+y'low));
         end loop;
      end if;
      return y;
   end function convert;
   function zero(tpl: int_array_t) return int_array_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;
   function convert(x: int_array_t; tpl: std_logic_vector_array) return std_logic_vector_array is
      variable y : std_logic_vector_array(tpl'range)(tpl(tpl'low)'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), (y(j)'range => '0'));
      end loop;
      return y;
   end function convert;
   function convert(x: std_logic_vector_array; tpl: int_array_t) return int_array_t is
      variable y : int_array_t(tpl'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), y(j));
      end loop;
      return y;
   end function convert;

   function width(x: patdef_array_t) return integer is
      variable w : integer := x'length * width(x(x'low));
   begin
      return w;
   end function width;
   function convert(x: patdef_array_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      constant W : natural := width(x(x'low));
      variable a : integer;
      variable b : integer;
   begin
      if y'ascending then
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(b to a), convert(x(i+x'low), y(b to a)));
         end loop;
      else
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(a downto b), convert(x(i+x'low), y(a downto b)));
         end loop;
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: patdef_array_t) return patdef_array_t is
      variable y : patdef_array_t(tpl'range);
      constant W : natural := width(y(y'low));
      variable a : integer;
      variable b : integer;
   begin
      if x'ascending then
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(b to a), y(i+y'low));
         end loop;
      else
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(a downto b), y(i+y'low));
         end loop;
      end if;
      return y;
   end function convert;
   function zero(tpl: patdef_array_t) return patdef_array_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;
   function convert(x: patdef_array_t; tpl: std_logic_vector_array) return std_logic_vector_array is
      variable y : std_logic_vector_array(tpl'range)(tpl(tpl'low)'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), (y(j)'range => '0'));
      end loop;
      return y;
   end function convert;
   function convert(x: std_logic_vector_array; tpl: patdef_array_t) return patdef_array_t is
      variable y : patdef_array_t(tpl'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), y(j));
      end loop;
      return y;
   end function convert;

   function width(x: segment_t) return natural is
      variable w : natural := 0;
   begin
      w := w + width(x.hits);
      w := w + width(x.partition);
      w := w + width(x.cnt);
      w := w + width(x.id);
      w := w + width(x.strip);
      return w;
   end function width;
   function convert(x: segment_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      variable w : integer;
      variable u : integer := tpl'left;
   begin
      if tpl'ascending then
         w := width(x.hits);
         y(u to u+w-1) := convert(x.hits, y(u to u+w-1));
         u := u + w;
         w := width(x.partition);
         y(u to u+w-1) := convert(x.partition, y(u to u+w-1));
         u := u + w;
         w := width(x.cnt);
         y(u to u+w-1) := convert(x.cnt, y(u to u+w-1));
         u := u + w;
         w := width(x.id);
         y(u to u+w-1) := convert(x.id, y(u to u+w-1));
         u := u + w;
         w := width(x.strip);
         y(u to u+w-1) := convert(x.strip, y(u to u+w-1));
      else
         w := width(x.hits);
         y(u downto u-w+1) := convert(x.hits, y(u downto u-w+1));
         u := u - w;
         w := width(x.partition);
         y(u downto u-w+1) := convert(x.partition, y(u downto u-w+1));
         u := u - w;
         w := width(x.cnt);
         y(u downto u-w+1) := convert(x.cnt, y(u downto u-w+1));
         u := u - w;
         w := width(x.id);
         y(u downto u-w+1) := convert(x.id, y(u downto u-w+1));
         u := u - w;
         w := width(x.strip);
         y(u downto u-w+1) := convert(x.strip, y(u downto u-w+1));
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: segment_t) return segment_t is
      variable y : segment_t;
      variable w : integer;
      variable u : integer := x'left;
   begin
      if x'ascending then
         w := width(tpl.hits);
         y.hits := convert(x(u to u+w-1), tpl.hits);
         u := u + w;
         w := width(tpl.partition);
         y.partition := convert(x(u to u+w-1), tpl.partition);
         u := u + w;
         w := width(tpl.cnt);
         y.cnt := convert(x(u to u+w-1), tpl.cnt);
         u := u + w;
         w := width(tpl.id);
         y.id := convert(x(u to u+w-1), tpl.id);
         u := u + w;
         w := width(tpl.strip);
         y.strip := convert(x(u to u+w-1), tpl.strip);
      else
         w := width(tpl.hits);
         y.hits := convert(x(u downto u-w+1), tpl.hits);
         u := u - w;
         w := width(tpl.partition);
         y.partition := convert(x(u downto u-w+1), tpl.partition);
         u := u - w;
         w := width(tpl.cnt);
         y.cnt := convert(x(u downto u-w+1), tpl.cnt);
         u := u - w;
         w := width(tpl.id);
         y.id := convert(x(u downto u-w+1), tpl.id);
         u := u - w;
         w := width(tpl.strip);
         y.strip := convert(x(u downto u-w+1), tpl.strip);
      end if;
      return y;
   end function convert;
   function zero(tpl: segment_t) return segment_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;

   function width(x: segment_list_t) return integer is
      variable w : integer := x'length * width(x(x'low));
   begin
      return w;
   end function width;
   function convert(x: segment_list_t; tpl: std_logic_vector) return std_logic_vector is
      variable y : std_logic_vector(tpl'range);
      constant W : natural := width(x(x'low));
      variable a : integer;
      variable b : integer;
   begin
      if y'ascending then
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(b to a), convert(x(i+x'low), y(b to a)));
         end loop;
      else
         for i in 0 to x'length-1 loop
            a := W*i + y'low + W - 1;
            b := W*i + y'low;
            assign(y(a downto b), convert(x(i+x'low), y(a downto b)));
         end loop;
      end if;
      return y;
   end function convert;
   function convert(x: std_logic_vector; tpl: segment_list_t) return segment_list_t is
      variable y : segment_list_t(tpl'range);
      constant W : natural := width(y(y'low));
      variable a : integer;
      variable b : integer;
   begin
      if x'ascending then
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(b to a), y(i+y'low));
         end loop;
      else
         for i in 0 to y'length-1 loop
            a := W*i + x'low + W - 1;
            b := W*i + x'low;
            y(i+y'low) := convert(x(a downto b), y(i+y'low));
         end loop;
      end if;
      return y;
   end function convert;
   function zero(tpl: segment_list_t) return segment_list_t is
   begin
      return convert(std_logic_vector'(width(tpl)-1 downto 0 => '0'), tpl);
   end function zero;
   function convert(x: segment_list_t; tpl: std_logic_vector_array) return std_logic_vector_array is
      variable y : std_logic_vector_array(tpl'range)(tpl(tpl'low)'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), (y(j)'range => '0'));
      end loop;
      return y;
   end function convert;
   function convert(x: std_logic_vector_array; tpl: segment_list_t) return segment_list_t is
      variable y : segment_list_t(tpl'range);
   begin
      for j in y'range loop
          y(j) := convert(x(j), y(j));
      end loop;
      return y;
   end function convert;

end package body pat_types;
