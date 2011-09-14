<?php

require("func.inc");

if (!are_in_state_b())
{
   header("Location: index.php");
   exit();
}

echo "<html><head><title>Welcome to B</title></head>";

echo "<body><div></div><p><span>You are in B's central area. Welcome to being a second class citizen</span></p></body>";

echo "</html>";

?>