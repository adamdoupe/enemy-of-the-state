<?php

error_reporting(E_ALL);

session_start();

?>

<html>
    <body>

<?php

if(isset($_REQUEST['logout'])) {
    $_SESSION['in'] = False;
} elseif(isset($_REQUEST['user']) && $_REQUEST['user'] == 'ludo' && $_REQUEST['pass'] == 'ludo') {
    echo 'ok';
    $_SESSION['in'] = True;
}

if(isset($_SESSION['in']) && $_SESSION['in']) {
?>
    <a href="private.php?logout=1">logout</a>

<?
} else {
?>

    <form method="post" action="private.php">
        <input type="text" name="user"/>
        <input type="text" name="pass"/>
        <input type="submit"/>
    </form>


<?php
}
?>
    <a href="root.html">back</a>
    <a href="a.html">a</a>
    </body>
</html>
