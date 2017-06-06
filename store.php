<?php
  include 'auth.php';
if (!CheckAccess())
  {

    //show the access denied message and exit script

    echo 'Access denied!';

    exit;

  }
else
  {
    $servername = "atlasusr.fis.utfsm.cl";
    $username = "orsosa"; // username for your database
    $password = "";
    $dbname = "telescopes"; // Name of database
#$now = new DateTime();

    $field = $_GET['field'];
    $value = $_GET['value'];

    $conn = mysql_connect($servername,$username,$password);
    if (!$conn)
      {
	die('Could not connect: ' . mysql_error());
      }
    $con_result = mysql_select_db($dbname, $conn);
    if(!$con_result)
      {
	die('Could not connect to specific database: ' . mysql_error());
      }

    #$datenow = $now->format("Y-m-d H:i:s");
    $hvalue = $value;

    $sql = "INSERT INTO usm_telescope_data ($field) VALUES ($value);";
    $result = mysql_query($sql);
    if (!$result) {
      die('Invalid query: ' . mysql_error());
    }
    echo "<h1>THE DATA HAS BEEN SENT!!</h1>";
    mysql_close($conn);
  }
?>
