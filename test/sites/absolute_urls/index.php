<?php

$link = "http://" . $_SERVER['SERVER_NAME'];
$port = "";
if ($_SERVER['SERVER_PORT'] != '80')
{
   $port =  ':' . $_SERVER['SERVER_PORT'];
}

$link = $link . $port . '/test/sites/absolute_urls/link.php';

?>

<html>
<head><title>Absolute URL test</title></head>
<body>
<div>
<a href="index.php">relative link to myself</a>
</div>
<div>
<a href="<?php echo $link; ?>">absolute link to next page</a>
</div>
</body>
</html>