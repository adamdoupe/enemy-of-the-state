<?php

class Pages 
{
   public $pages = array();
}

function get_page() 
{
   // only want one process accessing this at a time

   $lock = fopen("pages.lock", "w");
   flock($lock, LOCK_EX);
   
   $data = file_get_contents("pages.data");
   
   if ($data)
   {
      return unserialize($data);
   }
   else
   {
      return new Pages();
   }
}

function save_page($page)
{
   $lock = fopen("pages.lock", "w");
   flock($lock, LOCK_EX);

   $fp = fopen("pages.data", "w");
   fwrite($fp, serialize($page));
}

?>