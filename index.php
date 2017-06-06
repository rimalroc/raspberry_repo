<!doctype html>
<html>
<head>
	<meta charset='UTF-8' />
	<style>
		input, textarea {border:1px solid #CCC;margin:0px;padding:0px}

		#body {max-width:800px;margin:auto}
		#log {width:50%;height:50px}
		#message {width:100%;line-height:20px}
	</style>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
	<script src="fancywebsocket.js"></script>
	<script>
		var Server;
		var ids;
		var js_var;
		
		function updatevalues ( ) {
		ids = "";
		Server.send( 'message', "update");
		$.get("word.php", function(data) {
		document.getElementById("word").value = data;
		});
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
		        //                document.getElementById("datos").firstChild.nodeValue = payload;
		                if (ids == null)
		                      ids = payload.split(" ")[1];
		                else
		                      ids = ids + " " +  payload.split(" ")[1];
		                }else
		                       log( payload );
                                document.getElementById("ids").firstChild.nodeValue = ids;
                                document.getElementById("ids2").value = ids;
		});

			Server.connect();
		});
	</script>
</head>

<body>
	<div id='body'>
		<textarea id='log' name='log' readonly='readonly'></textarea><br/>
		<input type='text' id='message' name='message' />
		<input type='button' value='get list of channels' onclick='updatevalues();'>
	</div>
	<span id="datos">&nbsp;</span>
	
	<span id="ids">&nbsp</span>
	<form name="parameters" method="POST" action="interfaz.php" target="_parent">
	  <p>
	    <input type="text" id="ids2" name="ids" size="60" value="the list of entries with which you create the display page.">
	  </p>
	  <p>
	    <input type="submit" name="submit" value="Create display">
	  </p>
	  <input type="hidden" id="word" name="word" value="" >


	</form>

	
</body>

</html>
