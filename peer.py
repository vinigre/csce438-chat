#Please write your p2p chat client here 
#
#Must act as both a server and a client
import sys
import socket
import select

def prompt():
	sys.stdout.write("> ")
	sys.stdout.flush()

def connect_to_peer(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(2)
	try:
		sock.connect((host, port))
		ESTABLISHED_PEERS[sock] = (host, port)
	except:
		print("can't connect to peer", host, port, sys.exc_info()[0])
		print(type(host), type(port))
		sys.exit()

def print_help():
	#TODO
	print("command                     | function\n"
		  "----------------------------+------------------------------------\n"
		  "-help                       | displays this table\n"
		  "-online_users               | shows who is online\n"
		  "-connect [ip] [port]        | connect to a peer\n"
		  "-disconnect [ip] [port]     | disconnect from a peer\n"
		  "-talk [ip] [port] [message] | sends a message to a peer\n"
		  "-logoff                     | disconnect from the registry server")

if __name__ == "__main__":

	if len(sys.argv) < 3:
		print('Usage: python peer.py hostname port')
		sys.exit()

	mothership = sys.argv[1]  # mothership is the registry server
	port = int(sys.argv[2])

	CONNECTION_LIST = []  # necessary?
	ONLINE_PEERS = []  # list of tuples (addr, port)
	ESTABLISHED_PEERS = {}
	RECV_BUFFER = 4096

	mother_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	mother_sock.settimeout(2)

	try:
		mother_sock.connect((mothership, port))
	except:
		print('Unable to connect to registry server', sys.exc_info()[0])
		sys.exit()

	print('Connected to registry server.')

	ESTABLISHED_PEERS[mother_sock] = (mothership, port)
	ESTABLISHED_PEERS[sys.stdin] = ('', 0)

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind(('', 0))
	server_socket.listen(10)
	server_addr = server_socket.getsockname()[0]
	server_port = server_socket.getsockname()[1]

	ESTABLISHED_PEERS[server_socket] = (server_addr, server_port)
	print('I am:', server_addr, server_port)
	mother_sock.send(str(server_port).encode())

	while 1:
		read_sockets, write_sockets, error_sockets = select.select(ESTABLISHED_PEERS.keys(), [], [])

		for rsock in read_sockets:
			if rsock == mother_sock:
				#print('mother_sock')
				data = rsock.recv(RECV_BUFFER)
				if not data:
					del ESTABLISHED_PEERS[mother_sock]
				else:
					print("Online peers:\n", data.decode())
					prompt()
			elif rsock == server_socket:
				#print('server_sock')
				new_sock, addr = server_socket.accept()
				ESTABLISHED_PEERS[new_sock] = addr
			elif rsock == sys.stdin:
				#print('sys.stdin')
				data = sys.stdin.readline().strip()
				#print('data=' + data)
				command = data.split(' ', 1)[0]
				#print('data', data)
				if command == '-help':
					print_help()
				elif command == '-online_users':
					print('fetching online users')
					mother_sock.send("REQ::ONLINE_USERS".encode())
				elif command == '-connect':
					host = data.split(' ', -1)[1]
					port = int(data.split(' ', -1)[2])
					connect_to_peer(host, port)
				elif command == '-disconnect':
					host = data.split(' ', -1)[1]
					port = int(data.split(' ', -1)[2])
					for est_sock, est_addr in ESTABLISHED_PEERS.items():
						if est_addr == (host, port):
							del ESTABLISHED_PEERS[est_sock]
							break
					else:
						print("No such peer connected.")
				elif command == '-talk':
					host = data.split(' ', -1)[1]
					port = int(data.split(' ', -1)[2])
					mesg = data.split(' ', 3)[3]
					for est_sock, est_addr in ESTABLISHED_PEERS.items():
						if est_addr == (host, port):
							est_sock.send(mesg.encode())
							print('you:', mesg)
							break
					else:
						print("No such peer connected.")
				elif command == '-logoff':
					print('will logoff')
					mother_sock.send("REQ::LOGOFF".encode())
				else:
					print('invalid command:', command)
					print_help()
				prompt()
			else:
				data = rsock.recv(RECV_BUFFER)
				if not data:
					print('<disconnected from peer>')
					del ESTABLISHED_PEERS[rsock]
				else:
					#message from peer
					print(rsock.getsockname()[0], "says:", data.decode())

					#sys.stdout.write(data.decode())
					#sys.stdout.flush()
					#print(data.decode())
					prompt()

