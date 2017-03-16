#server.py

import SocketServer
import os, sys, commands
import account
import host_port
import getpass
import sys, json, re

class MyTCPHandler(SocketServer.BaseRequestHandler):
	exit_flag = False
	def handle(self): #override method handle
		print ("Connected from ", self.client_address) 
		while not self.exit_flag:
			msg = self.request.recv(1024) #recieve client command
			if not msg:
				break
			msg_parse = msg.split("|") #split msg by "|", like "ftp_authentication|username|passwd"
			msg_type = msg_parse[0]
			if hasattr(self, msg_type): #check if class contains the method
				func = getattr(self, msg_type)
				func(msg_parse) #call the method
			else:
				print "--\033[31;1mWrong msg type:%s\033[0m--" % msg_type

	def ftp_authentication(self, msg): #authenticate user
		auth_res = False
		if len(msg) == 3:
			msg_type, username, passwd = msg
			if account.accounts.has_key(username): #check if the username exists
				if account.accounts[username]['passwd'] == passwd: #check if passwd match the username
					auth_res = True
					self.login_user = username
					self.msg_rename = account.accounts[username]['rename']
					self.msg_mkdir = account.accounts[username]['mkdir']
					self.msg_upload = account.accounts[username]['upload']
					self.msg_download = account.accounts[username]['download']
					self.msg_delete = account.accounts[username]['delete']
					self.cur_path = username
					self.home_path = account.accounts[username]['home']
				else:
					auth_res = False #wrong passwd
			else:
				auth_res = False #wrong username
		else:
			auth_res = False #wrong command line

		if auth_res:
			msg = "%s::success" % msg_type
			print "\033[32;1muser:%s has passed authentication!\033[0m" % username
		else:
			msg = "%s::failed" % msg_type
		self.request.send(msg)

	def has_privilege(self, path):
		abs_path = os.path.abspath(path) #absolute path of the file
		if abs_path.startswith(self.home_path):
			return True
		else:
			return False

	def file_transfer(self, msg):
		transfer_type = msg[1]
		filename = "%s/%s" %(self.cur_path, msg[2])
		self.has_privilege(filename)
		if transfer_type == "get": #get --> client download the file
			if self.msg_download == "YES":
				if os.path.isfile(filename) and self.has_privilege(filename): #"FILENAME" is file and the path is right
					file_size = os.path.getsize(filename)
					confirm_msg = "file_transfer::get_file::send_ready::%s" % file_size
					#confirm_msg = "file_transfer::get_file::send_ready"
					self.request.send(confirm_msg)
					client_confirm_msg = self.request.recv(1024) #wait client to confirm
					
					if client_confirm_msg == "file_transfer::get_file::recv_ready":
						f = file(filename, "rb")
						size_left = file_size
						#print "Total size is %s bytes." %file_size
						while size_left > 0:
							if size_left >= 1024: #send 1024 bytes one time
								self.request.send(f.read(1024))
								size_left -= 1024
							else:
								self.request.send(f.read(size_left))
								size_left = 0
						else:
							print "---Send file: done---"
				else:
					err_msg = "file_transfer::get_file::error::file does not exist or is a directory"
					self.request.send(err_msg)
			else:
				err_msg = "file_transfer::get_file::error::unable to download the file"
				self.request.send(err_msg)

		elif transfer_type == "put": #put --> client upload the file
			if self.msg_upload == "YES":
				filename, file_size = msg[-2], int(msg[-1]) #file_transfer|put|send_ready|filename|file_size
				filename = "%s/%s" %(self.cur_path, filename)
				print "filename: ", filename
				if os.path.isfile(filename):
					f = file("%s.0" % (filename), "wb") #in case of override existing files
				else:
					f = file("%s" %(filename), "wb")
				confirm_msg = "file_transfer::put_file::recv_ready"
				self.request.send(confirm_msg)

				recv_size = 0
				while not recv_size == file_size:
					data = self.request.recv(1024) #recieve 1024 bytes once a time
					recv_size += len(data)
					f.write(data)
				else:
					print "--\033[32;1mReceiving file:%s done\033[0m--" %(filename)
					f.close()
			else:
				confirm_msg = "file_transfer::put_file::unable to upload the file"
				self.request.send(confirm_msg)

	def delete_file(self, msg): #del --> client delete file
		if self.msg_delete == "YES":
			print "-->delete file:", msg
			file_list = msg[1].split()
			for i in file_list:
				abs_file_path = "%s/%s" %(self.cur_path, i)
				cmd_res = commands.getstatusoutput("rm -rf %s"% abs_file_path)[1] #delete files through cmd line and return result
			confirm_msg = "delete::success"
		else:
			confirm_msg = "delete::failed::unable to delete the directory or the file"
		self.request.send(confirm_msg)

	def list_file(self, msg): #ls --> list files
		home_prefix = account.accounts[self.login_user]["home"]
		cmd = "cd %s;ls -la %s" % (self.cur_path, " ".join(msg[1:]))
		file_list = os.popen(cmd).read() #deal the cmd line and read
		confirm_msg = "message_transfer::ready::%s" % len(file_list)
		self.request.send(confirm_msg)
		confirm_from_client = self.request.recv(100)
		if confirm_from_client == "message_transfer::ready::client":
			self.request.sendall(file_list)

	def make_dir(self, msg): #mkdir -->make the directory
		if self.msg_mkdir == "YES":
			print "-->make directory:", msg
			dir_list = msg[1].split()
			for i in dir_list:
				abs_file_path = "%s/%s" %(self.cur_path, i)
				cmd_res = commands.getstatusoutput("mkdir %s" % abs_file_path)[1] #make dir through cmd line and return results
			if cmd_res:
				confirm_msg = "mkdir::failed::directory exists"
			else:
				confirm_msg = "mkdir::success"
		else:
			confirm_msg = "mkdir::failed::unable to make directory"
		self.request.send(confirm_msg)

	def rename(self, msg):  #rm --> rename directory or file
		if self.msg_rename == "YES":
			print "-->change file %s to %s" %(msg[1], msg[2])
			abs_file_path_old = "%s/%s" %(self.cur_path, msg[1])
			abs_file_path_new = "%s/%s" %(self.cur_path, msg[2])
			cmd_res = commands.getstatusoutput("mv %s %s" % (abs_file_path_old, abs_file_path_new))[1]
			confirm_msg = "rename::success"
		else:
			confirm_msg = "rename::failed::unable to rename the file"
		self.request.send(confirm_msg)

	def switch_dir(self, msg): #cd --> client switch directory
		switch_res = ""
		msg = msg[-1].split()
		if len(msg) == 1: # "cd" return to home directory
			self.cur_path = self.home_path
			relative_path = self.cur_path.split(self.home_path)[-1] #relative_path
			switch_res = "switch_dir::ok::%s" % relative_path
		
		elif len(msg) == 2:
			if os.path.isdir("%s/%s" %(self.cur_path, msg[-1])): #check if dir exists
				abs_path = os.path.abspath("%s/%s" %(self.cur_path, msg[-1]))
				if abs_path.startswith(self.home_path):
					self.cur_path = abs_path
					relative_path = self.cur_path.split(self.home_path)[-1]
					switch_res = "switch_dir::ok::%s" % relative_path
				else:
					switch_res = "switch_dir::error::target dir doesn't exist"
			else:
				switch_res = "switch_dir::error::target dir doesn't exist"
		else:
			switch_res = "switch_dir::error::Error:wrong command usage."
		self.request.send(switch_res)


class ServerSettings(): #the class about settings
	func_dic = {  #function dictionary
	"help" : "help",
	"add"  : "acc_add",
	"del"  : "acc_del",
	"show" : "show_attr",
	"port" : "port_change",
	"host" : "host_change",
	"pwd"  : "pwd_change",
	"attr" : "attr_change",
	"exit" : "exit"
	}

	def __init__(self):  #initialize
		self.exit_flag = False
		self.interactive()

	def interactive(self):  #deal with command line
		try:
			while not self.exit_flag:
				cmd = raw_input("\033[32;1m>>:\033[0m").strip()
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

	def acc_add(self, msg): #add user
		if len(msg) == 3:
			msg_type, username, passwd = msg #password can be seen
			if account.accounts.has_key(username):  #check if username is existed
				print "\033[31;1mAccount exists. \033[0m"
			else:
				attr = {"passwd" : passwd, "home" : "", "rename" : "YES", "mkdir" : "YES", 
				"upload" : "YES", "download" : "YES", "delete" : "YES"}
				addr = os.path.abspath("") + username
				attr["home"] = addr  #attributes of added user
				cur_addr = username
				
				while True:
					self.show(username, attr)
					confirm = raw_input("Confirm the information above about %s? Y/N: " %username) #confirm attributes information
					while confirm != "Y" and confirm != "N":   #Invalid input
						print "\033[31;1mInvalid msg. Please type Y or N again.\033[0m"
						confirm = raw_input("Confirm the information above about %s? Y/N: " %username)
					if confirm == "Y":   #confirmed information
						tmp = account.accounts
						tmp[username] = attr
						account.write(tmp)  #change "account.json" by calling module account.write()
						cmd_res = commands.getstatusoutput("mkdir %s" % cur_addr)[1]  #make the directory of new user
						break
					else:
						attr = self.attr_mod(attr)  #call method attr_mod()
				print "\033[32;1mAccount:%s has been added!\033[0m" % username
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def attr_mod(self, dict):   #change the attribute information about the user
		change = raw_input("Enter the attribute(s) name that you want to change: ").strip()
		if len(change) == 0:
			return dict
		change_parse = change.split()
		for i in change_parse:
			if not dict.has_key(i):   #Invalid attribute name
				print "\033[31;1mInvalid attribute name %s. Thus no change to it.\033[0m" % i
				continue
			elif i == "home":
				print "\033[31;1mUnable to change it.\033[0m"
			elif i == "passwd":
				passwd = raw_input("New password is: ")
				dict["passwd"] = passwd
			else:
				value = raw_input("Value of attribute %s is %s. Change it into YES/NO: " % (i, dict[i]))
				while value != "YES" and value != "NO":
					print "\033[31;1mInvalid attribute value. Type YES or NO again.\033[0m"
					value = raw_input("Value of attribute %s is %s. Change it into YES/NO: " % (i, dict[i]))
				dict[i] = value
		return dict

	def acc_del(self, msg): #delete user
		retry_count = 0
		if len(msg) == 2:
			msg_type, username = msg
			if account.accounts.has_key(username):
				while retry_count < 2:
					passwd = getpass.getpass()
					if account.accounts[username]["passwd"] == passwd:  #confirm user and passwd
						tmp = account.accounts

						confirm = raw_input("Delete directory of %s? Y/N: " % username)  #delete the directory of the user?
						while confirm != "Y" and confirm != "N":   #Invalid input
							print "\033[31;1mInvalid msg. Please type Y or N again.\033[0m"
							confirm = raw_input("Delete directory of %s? Y/N: " % tmp[username]["home"])
						if confirm == "Y":
							cmd_res = commands.getstatusoutput("rm -rf %s"% username)[1]
							print "\033[32;1mDirectory:%s has been deleted.\033[0m" % tmp[username]["home"]
						del tmp[username]   #delete information about the user
						account.write(tmp)  
						print "\033[32;1mAccount:%s has been deleted.\033[0m" % username
						break
					else:
						print "\033[31;1mWrong password, try it again.\033[0m"
						retry_count += 1
				else:
					print "\033[32;1mToo many attempts, please exit!\033[0m"
			else:
				print "\033[31;1mNo account named %s exists\033[0m" % username
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def port_change(self, msg):  #change port number
		if len(msg) == 1:
			print "\033[32;1mPort number is %d\033[0m" % host_port.info["port"]
		elif len(msg) == 2:
			msg_type, port_name = msg
			if port_name == "":
				port_name = 9000 #default port
			else:
				port_name = int(port_name)
				if port_name < 1025 or port_name > 65535: #Invalid number
					print "\033[31;1mInvalid ftp port number. 1024<port_number<65536.\033[0m"
				else:
					tmp = host_port.info
					tmp["port"] = port_name
					host_port.write(tmp)
					print "\033[32;1mPort number has been changed to %d\033[0m" % port_name 
		else:
			print "\033[31;1mWrong command usage\033[0m"
	
	def host_change(self, msg):  #change host number
		flag = False
		if len(msg) == 1:
			print "\033[32;1mHost name is %s\033[0m" % host_port.info["host"]
		elif len(msg) == 2:
			msg_type, host_name = msg
			if host_name == "":
				host_name = "127.0.0.1" #default host
			elif re.match(".*\..*\..*\..*", host_name) == None:
				print "\033[31;1mInvalid host name\033[0m"
			else:
				tmp = host_name.split(".")
				if len(tmp) == 4:
					for i in tmp:
						if not i.isdigit():
							print "\033[31;1mInvalid host name\033[0m"
						elif int(i) < 0 or int(i) > 255:
							print "\033[31;1mInvalid host name\033[0m"
						else:
							tmp = host_port.info
							tmp["host"] = host_name
							host_port.write(tmp)
							flag = True
					if flag:
						print "\033[32;1mHost name has been changed to %s\033[0m" % host_name
				else:
					print "\033[31;1mInvalid host name\033[0m"
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def show(self,username, attr):
		print '''                             
		Details information about %s is:
		home     %s
		passwd   %s
		Authentication for
		rename   %s
		mkdir    %s
		upload   %s
		download %s
		delete   %s
		''' % (username, attr["home"], attr["passwd"], attr["rename"], attr["mkdir"],
			attr["upload"], attr["download"], attr["delete"])   #show information about the user

	def show_attr(self, msg):  #show attribute value
		retry_count = 0
		if len(msg) == 2:
			msg_type, username = msg
			if account.accounts.has_key(username):
				while retry_count < 2:
					passwd = getpass.getpass()
					attr = account.accounts[username]
					if account.accounts[username]["passwd"] == passwd:  #confirm user and passwd
						if username == "root":
							confirm = raw_input("show all users' information? Y/N: ")
							while confirm != "Y" and confirm != "N":   #Invalid input
								print "\033[31;1mInvalid msg. Please type Y or N again.\033[0m"
								confirm = raw_input("show all users' information? Y/N: ")
							if confirm == "Y":
								for i in account.accounts:
									attr = account.accounts[i]
									self.show(i, attr)
								break
							elif confirm == "N":
								self.show(username, attr)
								break
						else:
							self.show(username, attr)
							break
					else:
						print "\033[31;1mWrong password, try it again.\033[0m"
						retry_count += 1
				else:
					print "\033[32;1mToo many attempts, please exit!\033[0m"
			else:
				print "\033[31;1mNo account named %s exists\033[0m" % username
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def attr_change(self, msg):   #change attribute value
		retry_count = 0
		if len(msg) == 2:
			msg_type, username = msg
			if account.accounts.has_key(username):
				while retry_count < 2:
					passwd = getpass.getpass()
					attr = account.accounts[username]
					if account.accounts[username]["passwd"] == passwd:  #confirm user and passwd
						attr = self.attr_mod(attr)  #call method attr_mod
						print '''                             
						Details information about %s is:
						home     %s
						Authentication for
						rename   %s
						mkdir    %s
						upload   %s
						download %s
						delete   %s
						''' % (username, attr["home"], attr["rename"], attr["mkdir"],
							attr["upload"], attr["download"], attr["delete"])   #show information about the user
						tmp = account.accounts
						tmp[username] = attr
						account.write(tmp)
						break
					else:
						print "\033[31;1mWrong password, try it again.\033[0m"
						retry_count += 1
				else:
					print "\033[32;1mToo many attempts, please exit!\033[0m"
			else:
				print "\033[31;1mNo account named %s exists\033[0m" % username
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def pwd_change(self, msg):  #change passwd of the user
		retry_count = 0
		if len(msg) == 2:
			msg_type, username = msg
			if account.accounts.has_key(username):
				while retry_count < 2:
					passwd = getpass.getpass()
					if account.accounts[username]["passwd"] == passwd:  #confirm user and passwd
						new_pwd = raw_input("Enter new password: ")
						tmp = account.accounts
						tmp[username]["passwd"] = new_pwd   #change passwd
						account.write(tmp)
						print "\033[32;1mAccount:%s passwd has been changed.\033[0m" % username
						break
					else:
						print "\033[31;1mWrong password, try it again.\033[0m"
						retry_count += 1
				else:
					print "\033[32;1mToo many attempts, please exit!\033[0m"
			else:
				print "\033[31;1mNo account named %s exists\033[0m" % username
		else:
			print "\033[31;1mWrong command usage\033[0m"

	def exit(self, msg):
		sys.exit()

	def help(self, msg):   #[help] information
		print '''
		help    help
		show    show account_name
		add     add account_name account_pwd
		del     del account_name
		exit    exit the system
		port    port port_number
		host    host host_name
		pwd     pwd account_name
		attr    attr account_name
		'''

if __name__ == "__main__":
	#HOST, PORT = "127.0.0.1", 9000
	choice = raw_input("Enter setting mode? Y/N:")
	print choice
	while choice != "Y" and choice != "N":    #Invalid input
		print "Invalid input. Please choose Y or N again."
		choice = raw_input("Enter setting mode? Y/N:")
	if choice == "N":     #connect with client
		HOST = host_port.info["host"]
		PORT = host_port.info["port"]
		server = SocketServer.ThreadingTCPServer((HOST, PORT), MyTCPHandler)
		server.serve_forever() #handle the request until shutdown
	else:   #Enter setting mode
		f = ServerSettings()
