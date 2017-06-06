<?php
  //This function returns True if query string contains secretkey and secretvalue.
  //Otherwise it returns False

  function CheckAccess()

  {
    return @$_POST['word']=='LetMeIn!';

  }

?>
