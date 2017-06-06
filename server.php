<?php
// prevent the server from timing out
set_time_limit(0);

// include the web sockets server script (the server is started at the far bottom of this file)
require 'class.PHPWebSocket.php';

// when a client sends data to the server
function wsOnMessage($clientID, $message, $messageLength, $binary) {
	global $Server;
	$ip = long2ip( $Server->wsClients[$clientID][6] );

	// check if message length is 0
	if ($messageLength == 0) {
		$Server->wsClose($clientID);
		return;
	}

	//The speaker is the only person in the room. Don't let them feel lonely.
	if ( sizeof($Server->wsClients) == 1 ){
//		$Server->wsSend($clientID, "There isn't anyone else in the room, but I'll still listen to you. --Your Trusty Server");
	}else{
		//Send the message to everyone but the person who said it
		foreach ( $Server->wsClients as $id => $client ){
			if ( $id != $clientID )
				$Server->wsSend($id, "Visitor $clientID ($ip) said \"$message\"");
		}
	}
	global $mysqli;
	if ($message === 'update')
	{
		//aqui hay que implementar in try catch, porque arrojo error una vez
		$result = $mysqli->query("SELECT *  FROM HV_channels_test_1");
    		while($row = $result->fetch_array(MYSQLI_NUM))
        	{
		       $rows[] = $row;
		              foreach ( $Server->wsClients as $id => $client )
			      	if ( $id == $clientID )
                      	       	      	$Server->wsSend($id, "mysql_update: $row[0] $row[1] $row[2] $row[3] $row[4] $row[5]");
		}
	}
	$tok = strtok($message," ");
        if ($tok === 'Vset')
	{
		$id = strtok(" ");
		$voltage = strtok(" ");
		$query = "UPDATE HV_channels_test_1 set Vset = $voltage where id = $id;";
//		printf($query);
                $result = $mysqli->query($query);
		
	}
		
}

// when a client connects
function wsOnOpen($clientID)
{
	global $Server;
	$ip = long2ip( $Server->wsClients[$clientID][6] );

	$Server->log( "$ip ($clientID) has connected." );

	//Send a join notice to everyone but the person who joined
	foreach ( $Server->wsClients as $id => $client )
		if ( $id != $clientID )
			$Server->wsSend($id, "Visitor $clientID ($ip) has joined the room.");
}

// when a client closes or lost connection
function wsOnClose($clientID, $status) {
	global $Server;
	$ip = long2ip( $Server->wsClients[$clientID][6] );

	$Server->log( "$ip ($clientID) has disconnected." );

	//Send a user left notice to everyone in the room
	foreach ( $Server->wsClients as $id => $client )
		$Server->wsSend($id, "Visitor $clientID ($ip) has left the room.");
}
//this function is not used, but is very usefull
function getServerAddress() {
if(array_key_exists('SERVER_ADDR', $_SERVER))
    return $_SERVER['SERVER_ADDR'];
    elseif(array_key_exists('LOCAL_ADDR', $_SERVER))
        return $_SERVER['LOCAL_ADDR'];
	elseif(array_key_exists('SERVER_NAME', $_SERVER))
	    return gethostbyname($_SERVER['SERVER_NAME']);
	    else {
	        // Running CLI
		    if(stristr(PHP_OS, 'WIN')) {
		            return gethostbyname(php_uname("n"));
			} else {
				 $ifconfig = shell_exec('/sbin/ifconfig eth0');
				 preg_match('/addr:([\d\.]+)/', $ifconfig, $match);
				 return $match[1];
			    }
	      }
}

//set up mysql connection
$username="PowerSupply";
$password="PSSiLab";
$database="PowerSupply_1";
$mysqli = new mysqli("localhost",$username,$password, "PowerSupply_1");
			    


// start the server
$Server = new PHPWebSocket();
$Server->bind('message', 'wsOnMessage');
$Server->bind('open', 'wsOnOpen');
$Server->bind('close', 'wsOnClose');
// for other computers to connect, you will probably need to change this to your LAN IP or external IP,
// alternatively use: gethostbyaddr(gethostbyname($_SERVER['SERVER_NAME']))

$ifconfig = shell_exec('/sbin/ifconfig eth0');
preg_match('/addr:([\d\.]+)/', $ifconfig, $match);
$ip = $match[1];
$Server->wsStartServer($ip, 9300);

?>