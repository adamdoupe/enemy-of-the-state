<html>
    <body>
<?php

echo '<p>'.$_GET['input'].'</p>';
echo '<a href="trap2.php?input='.($_GET['input']+1).'">next</a>';


?>
    <a href="<?php if($_GET['input'] > 1) {
        print 'trap2.php?input='.($_GET['input']-1);
    } else {
        print 'b.html';
    } ?>">back</a>
    </body>
</html>
