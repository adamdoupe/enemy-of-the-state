<?php

require("func.inc");

if (!are_in_state_a())
{
   header("Location: index.php");
   exit();
}

echo "<html><head><title>Welcome to A</title></head>";

echo "<body><div><p>You are in A's central area. Welcome to the state of being that is A</p></div></body>";

echo "</html>"


?>