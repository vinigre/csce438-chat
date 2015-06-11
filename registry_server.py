#Please write your registry server code here
#
#
import socket
import select

#TODO: add exception handling as needed


def tell_online_peers(sock):
	list_as_text = ""
	for val in ONLINE_PEERS.values():
		list_as_text += str(val) + "\n"
	sock.send(list_as_text.encode())


def log_user_off(sock):
	print("Logging off user:", ONLINE_PEERS[sock])
	CONNECTION_LIST.remove(sock)
	del ONLINE_PEERS[sock]


def log_user_in(sock, addr):
	CONNECTION_LIST.append(sock)
	ONLINE_PEERS[sock] = addr

if __name__ == "__main__":
	print("Hello, I am the registry server.")
	CONNECTION_LIST = []
	ONLINE_PEERS = {}
	RECV_BUFFER = 4096
	PORT = 5000

	#TODO: initialize server on a socket
	# create a socket
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# set server options
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# The host ip and port this service listens
	server_socket.bind(("0.0.0.0", PORT))
	# The backlog argument specifies the maximum number of queued connections and should be at least 0
	server_socket.listen(10)
	# Add server socket to the list of readable connections
	CONNECTION_LIST.append(server_socket)
	print("Chat server started on port " + str(PORT))

	#TODO: listen for incoming connections via select call

	while 1:
		read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

		for rsock in read_sockets:
			if rsock == server_socket:  # New connection to the reg_server
				new_sock, addr = server_socket.accept()
				print('Accepting new peer connection:', addr)
				log_user_in(new_sock, addr)
			else:  # Peer may be requesting online_users, or they are logging off
				data = rsock.recv(RECV_BUFFER)
				if data.decode() == "REQ::ONLINE_USERS":
					tell_online_peers(rsock)
				elif data.decode() == "REQ::LOGOFF":
					log_user_off(rsock)
				elif data.isdigit():
					new_port = int(data.decode())
					ONLINE_PEERS[rsock] = (ONLINE_PEERS[rsock][0], new_port)
				else:
					print("Lost connection with", ONLINE_PEERS[rsock])
					log_user_off(rsock)


	#message type 1: peer is coming online, notifying us. Include type-2 response
	#message type 2: peer is requesting list of online users
	#message type 3: peer is notifying us they are logging off
	#message type 4: peer reports that another peer from the online list is MIA (optional)
	#                If enough peers report someone as MIA, take off online list?