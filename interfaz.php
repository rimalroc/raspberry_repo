<!doctype html>

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

		a.toggler {
		background: green;
		cursor: pointer;
		border: 2px solid black;
		border-left-width: 20px;
		padding: 0 10px;
		border-radius: 4px;
		text-decoration: none;
		transition: all .2s ease;
		}

		a.toggler.off {
		background: red;
		border-right-width: 20px;
		border-left-width: 2px;
		}
		
		#body {max-width: 800px;
		}
		#log {width: 300px; height:100px; background: #EEE;}
		#message {width: 100%; line-height:20px}
		table {max-width: 800px;
		       background-color: #EEE
		}
		th, td {
		    border: 1px solid #AAA;
		}
		body {
		    background: #EEE;
		}
		span {
				background-color: #EEE
		}
	</style>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
	<script src="fancywebsocket.js"></script>
	<script type="text/javascript">
		var Server;
		var ids;
		var timestamp;
		var data = {}; //contain historical data per channel
                <?php
 		   $canales = $_POST["ids"];
		   $canal = strtok($canales, " ");
		   echo "\n";
		   while ($canal !== false){
		   echo "\t\tdata[\"$canal\"] = [];\n";
		   $canal = strtok(" ");
		   }
		   ?>

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

		//////////////////////////
		//generate a file on datafile with historical data from one channelid
		
		function generatefile (channelid) {
			properties = {type: 'plain/text'}; // Specify the file's mime-type.
			log("file generated for : " + channelid);
			try {
				// Specify the filename using the File constructor, but ...
				file = new File(data[channelid], "datafile.txt", properties);
			} catch (e) {
				// ... fall back to the Blob constructor if that isn't supported.
				file = new Blob(data[channelid], properties);
			}
			url = URL.createObjectURL(file);
			document.getElementById('file').href = url;
		}

		//to be excecuted whenever the document has been loaded and ready
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

		//////
		// Vset boxes
			<?php
			   $canales = $_POST["ids"];
			   $canal = strtok($canales, " ");
			   echo "\n";
			   while ($canal !== false){
			   echo "\t\t\t\t$('#Vs$canal').keypress(function(e) {\n";
			   echo "\t\t\t\tif ( e.keyCode == 13 && this.value ) {\n";
			   echo "\t\t\t\t\tlog( 'You are trying to set voltage: ' + this.value );\n";
			   echo "\t\t\t\t\tcommand = \"Vset \" + $canal + \" \" +this.value;\n";
			   echo "\t\t\t\t\tsend( command );\n";
			   echo "\t\t\t\t\tlog (command);\n";
			   echo "\t\t\t\t\t$(this).val(''); }\n";
			   echo "\t\t\t\t});\n\n";
			   $canal = strtok(" ");
			   }
			   ?>
			////////////////////
			//On Off switches
			
			<?php
			   $canales = $_POST["ids"];
			   $canal = strtok($canales, " ");
			   echo "\n";
			   while ($canal !== false){
			   echo "\t\t\t\t$('#onoff$canal').click(function() {\n";
			   echo "\t\t\t\t\t$(this).toggleClass('off');\n";
			   echo "\t\t\t\t\tif (this.className === 'toggler') {\n";
			   echo "\t\t\t\t\tthis.innerHTML = \"ON \";\n";
			   echo "\t\t\t\t\t\tlog( 'You are trying to toggle on: ');\n";
			   echo "\t\t\t\t\t\tcommand = \"enable \" + $canal + \" \" + 1;\n";
			   echo "\t\t\t\t\t\tsend( command );\n";
			   echo "\t\t\t\t\t\tlog (command);\n";
			   echo "\t\t\t\t\t}\n";
			   echo "\t\t\t\t\tif (this.className === 'toggler off') {\n";
			   echo "\t\t\t\t\tthis.innerHTML = \"OFF\";\n";
			   echo "\t\t\t\t\t\tlog( 'You are trying to toggle off: ');\n";
			   echo "\t\t\t\t\t\tcommand = \"enable \" + $canal + \" \" + 0;\n";
			   echo "\t\t\t\t\t\tsend( command );\n";
			   echo "\t\t\t\t\t\tlog (command);\n";
			   echo "\t\t\t\t\t}\n";
			   echo "\t\t\t\t});\n\n";
			   $canal = strtok(" ");
			   }
			   ?>
		
			//Let the user know we're connected
			Server.bind('open', function() {
				log( "Connected." );
			});

			//OH NOES! Disconnection occurred.
			Server.bind('close', function( data ) {
				log( "Disconnected." + document.getElementById("timestamp").firstChild.nodeValue );
			});

			//compute messages sent from server
			Server.bind('message', function( payload ) {
				if ( payload.split(" ")[0] == "mysql_update:" ){

					if (ids == null)
						ids = payload.split(" ")[1];
					else
						ids = ids + " " +  payload.split(" ")[1];
				<?php
				   $canales = $_POST["ids"];
				   $canal = strtok($canales, " ");
				   echo "\n";
				   while ($canal !== false){
				   echo "\t\t\t\t\tif ( payload.split(\" \")[1] == \"$canal\") {\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_mod\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[1];\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_ch\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[2];\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_en\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[3];\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_Vset\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[4];\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_Vmon\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[5];\n";
				   echo "\t\t\t\t\t\tdocument.getElementById(\"${canal}_Imon\").firstChild.nodeValue =  payload.split(\",\")[1].split(\" \")[6];\n";
				   echo "\t\t\t\t\t\tdata[\"$canal\"].push(timestamp + \" \" + payload.split(\",\")[1] + \"\\r\\n\");\n";
				   echo "\t\t\t\t\t}\n";
				   $canal = strtok(" ");
				   }
				   ?>
				}else if ( payload.split(" ")[0] == "time_update:" ){
					document.getElementById("timestamp").firstChild.nodeValue =  payload.split(" ")[1];
					timestamp = payload.split(" ")[1];
				}else
					log( payload );
                                document.getElementById("ids").firstChild.nodeValue = ids;

			});

			Server.connect();
		});

		
	</script>

  <img src="logo-usm1.jpg" height="150">
  <img src="Logo-CCTVal.png" height="150">

</head>
<body onload="setInterval('updatevalues()',1000);">
<p>
  <?php
     	   echo "<span id=\"username\"> Hola, Hello, Bonjour, Privet, ";
	   echo $_POST["username"];
	   echo "</span>\n";
     ?>
  </p>
	<table>
		<tr>
			<th hidden>channel id</th>
			<th>Module</th>
			<th>Channel</th>
			<th>enable</th>
			<th>V set</th>
			<th>V monitor</th>
			<th>I monitor</th>
			<th>V set (modify)</th>
		</tr>
	<?php
	   $canales = $_POST["ids"];
	   //         echo "$canales\n";
	   $canal = strtok($canales, " ");
	   while ($canal !== false){
	     echo "\t\t<tr>\n";
	     echo "\t\t\t<th hidden>$canal</th>\n";
	     echo "\t\t\t<th><span id='${canal}_mod'> </span></th>\n";
	     echo "\t\t\t<th><span id='${canal}_ch'> </span></th>\n";
	     echo "\t\t\t<th><span id='${canal}_en'> </span></th>\n";
	     echo "\t\t\t<th><span id='${canal}_Vset'> </span></th>\n";
	     echo "\t\t\t<th><span id='${canal}_Vmon'> </span></th>\n";
	     echo "\t\t\t<th><span id='${canal}_Imon'> </span></th>\n";
	     echo "\t\t\t<th><input type='text' id='Vs$canal' name='message' /></th>\n";
	     echo "\t\t\t<th><a href=\"#\" id='onoff$canal' class=\"toggler off\">OFF</a></th>\n";
	     echo "\t\t\t<th><input type=\"button\" name=\"filesubmit\" value=\"Create file\" onclick='generatefile(\"$canal\");'></th>\n";
	     echo "\t\t</tr>\n";
	     $canal = strtok(" ");
	   }
	?>
	</table>
	<div>
	  <p>
	    Create a file with historical data for a single channel pressing create file button<br>and then click in the following link:<br>
	    <a id="file" target="_blank" download="file.txt">Download File</a>
	  </p>
	</div>
	<div id='body'>
		<textarea id='log' name='log' readonly='readonly'></textarea><br/>
<!--		<input type='text' id='message' name='message' />
		<input type='button' value='get list of channels' onclick='updatevalues();'>
-->
	</div>
        epoch: <span id="timestamp">epoch</span>

</body>
</html>
