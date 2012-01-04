<?php

$error = False;
if (isset($_POST['firstname']) && isset($_POST['username']) && isset($_POST['password']) && isset($_POST['againpass']) && isset($_POST['lastname'])
    && $_POST['username'] && $_POST['password'] && $_POST['againpass'] && $_POST['firstname'] && $_POST['lastname'])
{
   if ($_POST['password'] != $_POST['againpass'])
   {
      $flash['error'] = "The passwords do not match. Try again";
      $error = True;
   }
   else if (True)
   {
	  header("Location: success.php", True, 303);
	  exit(0);
   }
   else
   {
	  $flash['error'] = "Username '{$_POST['username']}' is already in use.";
	  $error = True;
   }
}
else
{
   $flash['error'] = "All fields are required";
   $error = True;
}

if ($error)
{
?>
<html>
<head><title>I am the registration page</title></head>
<body>

<div>
<h2> Register for an account!</h2>
<?php 
if ($flash['error']) 
{
   echo htmlspecialchars($flash['error']);
}
?>
<table cellspacing="0" style="width:320px">
  <form action="<?php echo htmlspecialchars( $_SERVER['PHP_SELF'] )?>" method="POST">
  <tr><td>Username :</td><td> <input type="text" name="username" /></td></tr>
  <tr><td>First Name :</td><td> <input type="text" name="firstname" /></td></tr>
  <tr><td>Last Name :</td><td> <input type="text" name="lastname" /></td></tr>
  <tr><td>Password :</td><td> <input type="password" name="password" /></td></tr>
  <tr><td>Password again :</td><td> <input type="password" name="againpass" /></td></tr>
  <tr><td><input type="submit" value="Create Account!" /></td><td></td></tr>
</form>
</table>
</div>


</html>
<?php
}
?>