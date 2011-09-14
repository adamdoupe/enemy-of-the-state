<?php

  /* This is going to be a simple website with 3 pages where POSTing a link on one page 
     adds a link to another page. 
   */

require("pages.inc");

echo "<html><head><title>simple test</title></head><body>";


/* List all the pages */

$pages = get_page();
foreach ($pages->pages as $page)
{
   echo "<div><p><ul><li><a href='viewpage.php?id=" . $page . "'>page " . $page . "</a></li></ul></p></div>";
}

/* Link to add a page */

//echo "<form action='addpage.php' method='POST'><input type='submit' name='submit' value='add page' /></form>";
echo "<a href='addpage.php'>add a page</a><br />";

/* Static link */
echo "<a href='static.php'>always static</a>";

echo "</body></html>";
?>