<?php
   include 'auth.php';
   if (!CheckAccess())
   {
   echo 'Access denied!';
   exit;
   }
   ?>
<!DOCTYPE HTML>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    	<meta charset='UTF-8' />
	<style type="text/css">
		input, textarea {border:1px solid #CCC;margin:0px;padding:0px}

		#body {max-width:800px;margin:auto}
		#log {width:100%;height:100px}
		#message {width:100%;line-height:20px}
		table {max-width:800px;margin:100px}
		th, td {
		    border: 1px solid #AAA;
		    }
	</style>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
	<script src="fancywebsocket.js"></script>
	<script type="text/javascript">
		var Server;
		var ids;

		function updatevalues ( ) {
		ids = null;
		Server.send( 'message', "update");
		}

		function log( text ) {
			$log = $('#log');
			//Add text to log
			$log.append(($log.val()?"\n":'')+text);
			//Autoscroll
			$log[0].scrollTop = $log[0].scrollHeight - $log[0].clientHeight;
		}

		function send( text ) {
			Server.send( 'message', text );
		}

		$(document).ready(function() {
			log('Connecting...');
			var ip = "<?php $ifconfig = shell_exec('/sbin/ifconfig eth0');
                           preg_match('/addr:([\d\.]+)/', $ifconfig, $match);
                           $ip = $match[1];
                           echo $ip; ?>";
			Server = new FancyWebSocket('ws://' + ip + ':9300');


			$('#message').keypress(function(e) {
				if ( e.keyCode == 13 && this.value ) {
					log( 'You: ' + this.value );
					send( this.value );

					$(this).val('');
				}
			});
			$('#submit').keypress(function(e) {
		                        Server.send( 'message', "update");
			});
                <?php
 		   $canales = $_POST["ids"];
		   $canal = strtok($canales, " ");
		   while ($canal !== false){
		   echo "\t$('#Vs$canal').keypress(function(e) {\n";
		   echo "\tif ( e.keyCode == 13 && this.value ) {\n";
		   echo "\t\tlog( 'You are trying to set voltage: ' + this.value );\n";
		   echo "\t\tcommand = \"Vset \" + $canal + \" \" +this.value;\n";
		   echo "\t\tsend( command );\n";
		   echo "\t\tlog (command);\n";
		   echo "\t\t$(this).val(''); }\n";
		   echo "\t});\n\n";
		   $canal = strtok(" ");
		   }
		   ?>
		
			//Let the user know we're connected
			Server.bind('open', function() {
				log( "Connected." );
			});

			//OH NOES! Disconnection occurred.
			Server.bind('close', function( data ) {
				log( "Disconnected." );
			});

			//Log any messages sent from server
			Server.bind('message', function( payload ) {
		                if ( payload.split(" ")[0] == "mysql_update:" ){

		                   if (ids == null)
		                      ids = payload.split(" ")[1];
		                   else
		                      ids = ids + " " +  payload.split(" ")[1];
                <?php
                   $canales = $_POST["ids"];
                   $canal = strtok($canales, " ");
                   while ($canal !== false){
		       echo "\tif ( payload.split(\" \")[1] == \"$canal\") {\n";
                       echo "\t\tdocument.getElementById(\"$canal\").firstChild.nodeValue =  payload.split(\"$canal\")[1];\n";
                       echo "\t}\n";
		       $canal = strtok(" ");
		   }
		?>
				}else
		                    log( payload );
                                document.getElementById("ids").firstChild.nodeValue = ids;

			});

			Server.connect();
		});

	</script>
</head>
<body onload="setInterval('updatevalues()',1000);">


	<table>
		<tr>
			<th>channel id</th>
			<th>parameters</th>
			<th>V set</th>
		</tr>
	<?php
	   //         echo 'Hola ' . $_POST["ids"] . '!';
	   $canales = $_POST["ids"];
	   //         echo "$canales\n";
	   $canal = strtok($canales, " ");
	   while ($canal !== false){
	   echo "<tr>\n";
	   echo "<th>$canal</th>\n";
	   echo "<th><span id='$canal'> </span></th>\n";
	   echo "<th><input type='text' id='Vs$canal' name='message' /></th>\n";

	   $canal = strtok(" ");
	   echo "</tr>\n";
	   }
	   ?>
	</table>

	<div id='body'>
		<textarea id='log' name='log' readonly='readonly'></textarea><br/>
		<input type='text' id='message' name='message' />
		<input type='button' value='get list of channels' onclick='updatevalues();'>
	</div>
        <span id="ids">&nbsp</span>

</body>
</html>
