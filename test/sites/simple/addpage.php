<?php
require("pages.inc");

$pages = get_page();
$len = count($pages->pages);
$pages->pages[$len] = $len;

save_page($pages);

header("Location: index.php");

?>