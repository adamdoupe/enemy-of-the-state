<?php if (!isset($_GET['id']))
{
   header("Location: index.php");
}
else
{
   require ("pages.inc");
   $pages = get_page();
   $id = intval($_GET['id']);
   $len = count($pages->pages);
   if (!($id >= 0 && $id < $len))
   {
      header("Location: index.php");
   }
   else
   {
      echo "<html><head><title>Hello page " . $id . "</title></head>";
      echo "<body><h1>I AM PAGE " . $id . "</h1></body></html>";
   }



}
?>