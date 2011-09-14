<?php
require("func.inc");

echo "<html><head><title>Welcome to a state test</title></head>";

echo "<body>";


if (are_in_state_a())
{
   echo "<a href='a.php'>This is a link to A because we're in state A.</a><br/>";
}
else
{
   echo "<a href='b.php'>This is a link to B because we're in state B.</a><br/>";
}

echo "<div><a href='changestate.php'>Change the state!</a></div>";

echo "</body></html>";



?>