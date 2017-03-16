#client.py

import socket
import os, sys
import getpass

class FtpClient(object):

	func_dic = {  #function dictionary
	"help" : "help",
	"get" : "get_file",
	"put" : "put_file",
	"exit" : "exit",
	"ls" : "list_file",
	"cd" : "switch_dir",
	"del" : "delete",
	"mkdir" : "make_dir",
	"mv" : "rename"
	}

	def __init__(self, host, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		self.sock.connect((host, port)) #connect server
		self.exit_flag = False
		if self.auth():
			self.interactive()

	def list_file(self, msg): #list file(s)
		instruction = "list_file|%s" %(" ".join(msg[1:])) #list >= one file
		self.sock.send(instruction)
		server_confirm_msg = self.sock.recv(100)
		if server_confirm_msg.startswith("message_transfer::ready"):
			server_confirm_msg = server_confirm_msg.split("::")
			msg_size = int(server_confirm_msg[-1]) #message_transfer::ready::len(file_list)
			self.sock.send("message_transfer::ready::client")

			recv_size = 0
			while not msg_size == recv_size:
				if msg_size - recv_size > 1024:
					data = self.sock.recv(1024)
				else:
					data = self.sock.recv(msg_size - recv_size)
				recv_size += len(data)
				sys.stdout.write(data)

	def switch_dir(self, msg): #switch directory
		self.sock.send("switch_dir|%s" % " ".join(msg)) #one | more than one msg
		feedback = self.sock.recv(100)
		if feedback.startswith("switch_dir::ok"):
			self.cur_path = feedback.split("::")[-1] #result
			print self.cur_path
		else:
			print "\033[31;1m%s\033[0m" % feedback.split("::")[-1]

	def delete(self, msg): #delete files
		if len(msg) > 1:
			instruction = "delete_file|%s" % " ".join(msg[1:]) #delete >= one file
			self.sock.send(instruction)
			feedback = self.sock.recv(1024) #wait server to confirm
			if feedback.startswith("delete::success"):
				name = " ".join(msg[1:])
				print "\033[32;1mFile/Directory %s deleted.\033[0m" % name
			else:
				print "\033[31;1m%s\033[0m" % feedback
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def make_dir(self, msg): #make new directory
		if len(msg) > 1:
			instruction = "make_dir|%s" % " ".join(msg[1:]) #make >= one dir
			self.sock.send(instruction)
			feedback = self.sock.recv(1024) #wait server to confirm
			if feedback.startswith("mkdir::success"):
				name = " ".join(msg[1:])
				print "\033[32;1mDirectory %s is made.\033[0m" % name
			else:
				print "\033[31;1m%s\033[0m" % feedback
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def rename(self, msg):
		if len(msg) == 3:
			instruction = "rename|%s|%s" % (msg[1], msg[2])
			self.sock.send(instruction)
			feedback = self.sock.recv(1024) #wait server to confirm
			if feedback.startswith("rename::success"):
				print "\033[32;1mFile %s is changed into %s.\033[0m" % (msg[1], msg[2])
			else:
				print "\033[31;1m%s\033[0m" % feedback
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def auth(self): #authenticate user
		retry_count = 0
		while retry_count < 3: #has 3 times to try
			username = raw_input("username:").strip()
			if len(username) == 0:
				continue
			passwd = getpass.getpass() #show no passwd while entering
			auth_str = "ftp_authentication|%s|%s" %(username, passwd)
			
			self.sock.send(auth_str)
			auth_feedback = self.sock.recv(1024) #wait confirm msg

			if auth_feedback == "ftp_authentication::success":
				print "\033[32;1mAuthentication Passed!\033[0m"
				self.username = username
				self.cur_path = username
				return True
			else:
				print "\033[32;1mWrong username or password\033[0m"
				retry_count += 1
		else:
			print "\033[32;1mToo many attempts, please exit!\033[0m"

	def interactive(self):
		try:
			while not self.exit_flag:
				cmd = raw_input("\033[32;1m%s\033[0m%s]>>:" % (self.username, self.cur_path)).strip()
				if len(cmd) == 0:
					continue
				cmd_parse = cmd.split() #split the command line
				msg_type = cmd_parse[0]

				if self.func_dic.has_key(msg_type):#check if class has the method
					func = getattr(self, self.func_dic[msg_type])
					func(cmd_parse) #call the method
				else:
					print "Invalid instruction, type [help] to see available cmd list."
		except KeyboardInterrupt: #ctrl+c
			self.exit("exit")
		except EOFError: #end of file
			self.exit("exit")			

	def get_file(self, msg): #download the file
		if len(msg) == 2:
			msg = "file_transfer|get|%s" % msg[1]
			self.sock.send(msg)
			feedback = self.sock.recv(1024) #wait server to confirm
			if feedback.startswith("file_transfer::get_file::send_ready"): #server is ready to send file
				file_size = int(feedback.split("::")[-1])
				filename = os.path.basename(msg.split("|")[-1])
				f = file(filename, "wb")
				self.sock.send("file_transfer::get_file::recv_ready") #tell server that client is ready
				recv_size = 0
				progress_percent = 0
	
				while not file_size == recv_size:
					data = self.sock.recv(file_size - recv_size) #1024 bytes every time
					recv_size += len(data)
					f.write(data)
					cur_percent = int(float(recv_size) / file_size * 100)
					if cur_percent > progress_percent:
						progress_percent = cur_percent
						self.show_progress(file_size, recv_size, progress_percent) #show progress of downloading
				else:
					print "Received the file done"
					f.close()
			else:
				print "\033[31;1m%s\033[0m" % feedback
	
	def put_file(self, msg): #upload the file
		if len(msg) == 2:
			if os.path.isfile(msg[1]):
				file_size = os.path.getsize(msg[1])
				instruction_msg = "file_transfer|put|send_ready|%s|%s" %(msg[1], file_size)
				self.sock.send(instruction_msg)
				feedback = self.sock.recv(1024)
				print "==>", feedback

				progress_percent = 0
				if feedback.startswith("file_transfer::put_file::recv_ready"):
					f = file(msg[1], "rb")
					sent_size = 0
					while not sent_size == file_size: #send 1024 bytes once a time
						if file_size - sent_size <= 1024: 
							data = f.read(file_size - sent_size)
							sent_size += file_size - sent_size
						else:
							data = f.read(1024)
							sent_size += 1024
						self.sock.send(data)

						cur_percent = int(float(sent_size) / file_size * 100)
						if cur_percent > progress_percent:
							progress_percent = cur_percent
							self.show_progress(file_size, sent_size, progress_percent)
					else:
						print "--send file: %s done---" % msg[1]
					f.close()
				else:
					print "\033[31;1m%s\033[0m" % feedback
			else:
				print "\033[32;1mFile %s doesn't exist on local disk.\033[0m" % msg[1]

	def show_progress(self, total, finished, percent): #show the downloaded/uploaded progress
		progress_mark = "=" * (percent/2)
		sys.stdout.write("[%sbytes/%sbytes]%s>%s\r" % (total, finished, progress_mark, percent))
		sys.stdout.flush()
		if percent == 100:
			print "\n"

	def exit(self, msg):
		self.sock.shutdown(socket.SHUT_WR) #shut down the system
		sys.exit("Bye! %s" % self.username)

	def help(self, msg):
		print '''
		help    help
		get     get remote_filename
		put     put local_filename
		exit    exit the system
		ls      list all the files in current directory
		cd      cd some_dir
		del     del remote_filename
		mkdir   mkdir dirname
		mv      rename old_name new_name
		'''

if __name__ == "__main__":
	#ftp_addr = raw_input("Enter ftp address. Format: ftp://<hostname>/n")
	#ftp_addr = ftp_addr.split("ftp://")
	#host = ftp_addr[1]
	host = "127.0.0.1"
	f = FtpClient(host, 9000)
