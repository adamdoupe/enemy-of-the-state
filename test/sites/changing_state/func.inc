<?php

$lock = fopen(".lock", "w");
flock($lock, LOCK_EX);

function are_in_state_a()
{
   return file_exists("a");
}

function are_in_state_b()
{
   return !are_in_state_a();
}

function change_state()
{
   if (are_in_state_a())
   {
      set_state_b();
   }
   else 
   {
      set_state_a();
   }
}

function set_state_b()
{
   unlink("a");
}

function set_state_a()
{
   touch("a");
}


?>