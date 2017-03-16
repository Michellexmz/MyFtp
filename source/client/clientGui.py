#client.py
# --*--codig: utf8 --*--

from PyQt4 import QtGui
from PyQt4.QtCore import *
import socket
import os, sys, commands
import re
from dialog import loginDialog, ProgressDialog, DownloadProgressWidget, UploadProgressWidget, nameEditDialog
from get_fileProperty import fileProperty

app_icon_path = os.path.join(os.path.dirname(__file__), 'icons')

# The BaseGuiWidget provide LocalGuiWidget and RemoteGuiWidget to inheritance
class BaseGuiWidget(QtGui.QWidget):
	def __init__(self, parent=None):
		super(BaseGuiWidget, self).__init__(parent)
		self.resize(600, 600)
		self.createFileListWidget()
		self.createGroupboxWidget()

		# setting column width
		for pos, width in enumerate((150, 70, 70, 70, 90, 90)):
			self.fileList.setColumnWidth(pos, width)

		self.mainLayout = QtGui.QVBoxLayout()
		self.mainLayout.addWidget(self.groupBox)
		self.mainLayout.addWidget(self.fileList)
		self.mainLayout.setMargin(5)
		self.setLayout(self.mainLayout)

		# completer for path edit
		completer = QtGui.QCompleter()
		self.completerModel = QtGui.QStringListModel()
		completer.setModel(self.completerModel)
		self.pathEdit.setCompleter(completer)

	def createGroupboxWidget(self):
		self.pathEdit   = QtGui.QLineEdit()
		self.homeButton = QtGui.QPushButton()
		self.backButton = QtGui.QPushButton()
		self.nextButton = QtGui.QPushButton()
		self.homeButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'home.png')))
		self.backButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'back.png')))
		self.nextButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'next.png')))
		self.homeButton.setIconSize(QSize(20, 20))
		self.homeButton.setEnabled(False)
		self.backButton.setEnabled(False)
		self.nextButton.setEnabled(False)
		self.hbox1 = QtGui.QHBoxLayout()
		self.hbox2 = QtGui.QHBoxLayout()
		self.hbox1.addWidget(self.homeButton)
		self.hbox1.addWidget(self.pathEdit)
		self.hbox2.addWidget(self.backButton)
		self.hbox2.addWidget(self.nextButton)
		self.hbox2.addSpacerItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))

		self.gLayout = QtGui.QVBoxLayout()
		self.gLayout.addLayout(self.hbox1)
		self.gLayout.addLayout(self.hbox2)
		self.gLayout.setSpacing(5)
		self.gLayout.setMargin(5)
		self.groupBox = QtGui.QGroupBox('Widgets')
		self.groupBox.setLayout(self.gLayout)

	def createFileListWidget(self):
		self.fileList = QtGui.QTreeWidget()
		self.fileList.setIconSize(QSize(20, 20))
		self.fileList.setRootIsDecorated(False)
		self.fileList.setHeaderLabels(('Name', 'Size', 'Owner', 'Group', 'Time', 'Mode'))
		self.fileList.header().setStretchLastSection(False)

class LocalGuiWidget(BaseGuiWidget):
	def __init__(self, parent=None):
		BaseGuiWidget.__init__(self, parent)
		self.uploadButton  = QtGui.QPushButton()
		self.connectButton = QtGui.QPushButton()
		self.uploadButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'upload.png')))
		self.connectButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'connect.png')))
		self.hbox2.addWidget(self.uploadButton)
		self.hbox2.addWidget(self.connectButton)
		self.groupBox.setTitle('Local')

class RemoteGuiWidget(BaseGuiWidget):
	def __init__(self, parent=None):
		BaseGuiWidget.__init__(self, parent)
		self.downloadButton = QtGui.QPushButton()
		self.downloadButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'download.png')))
		self.homeButton.setIcon(QtGui.QIcon(os.path.join(app_icon_path, 'internet.png')))
		self.hbox2.addWidget(self.downloadButton)
		self.groupBox.setTitle('Remote')

class FtpClient(QtGui.QWidget):
	def __init__(self, parent = None):
		super(FtpClient, self).__init__(parent)
		self.setupGui()
		self.downloads = []
		self.remote.homeButton.clicked.connect(self.cdToRemoteHomeDirectory)
		self.remote.fileList.itemDoubleClicked.connect(self.cdToRemoteDirectory)
		self.remote.backButton.clicked.connect(self.cdToRemoteBackDirectory)
		self.remote.nextButton.clicked.connect(self.cdToRemoteNextDirectory)
		self.remote.fileList.itemClicked.connect(lambda: self.remote.downloadButton.setEnabled(True))
		self.remote.fileList.setContextMenuPolicy(Qt.CustomContextMenu)
		self.remote.fileList.customContextMenuRequested.connect(self.on_remoteList_customContextMenuRequested)
		self.remote.downloadButton.clicked.connect(self.download)
		QObject.connect(self.remote.pathEdit, SIGNAL('returnPressed( )'), self.cdToRemotePath)

		self.local.homeButton.clicked.connect(self.cdToLocalHomeDirectory)
		self.local.fileList.itemDoubleClicked.connect(self.cdToLocalDirectory)
		self.local.fileList.itemClicked.connect(lambda: self.local.uploadButton.setEnabled(True))
		self.local.backButton.clicked.connect(self.cdToLocalBackDirectory)
		self.local.nextButton.clicked.connect(self.cdToLocalNextDirectory)
		self.local.fileList.setContextMenuPolicy(Qt.CustomContextMenu)
		self.local.fileList.customContextMenuRequested.connect(self.on_localList_customContextMenuRequested)
		self.local.uploadButton.clicked.connect(self.upload)
		self.local.connectButton.clicked.connect(self.connect)
		QObject.connect(self.local.pathEdit, SIGNAL('returnPressed( )'), self.cdToLocalPath)
		
		#self.progressDialog = ProgressDialog(self)		

		self.localBrowseRec = []
		self.localBackCount = 0
		self.local_pwd = os.getenv('HOME')
		self.localOriginPath = self.local_pwd
		self.localBrowseRec.append(self.local_pwd)
		self.loadToLocaFileList()

	def setupGui(self):
		self.resize(1200, 650)
		self.local  = LocalGuiWidget(self)
		self.remote = RemoteGuiWidget(self)
		mainLayout = QtGui.QHBoxLayout()
		mainLayout.addWidget(self.remote)
		mainLayout.addWidget(self.local)
		mainLayout.setSpacing(0)
		mainLayout.setMargin(5)
		self.setLayout(mainLayout)

	def initialize(self):
		self.remoteBackCount = 0
		self.remoteBrowseRec = []
		self.pwd = self.cur_path
		self.remoteOriginPath = self.pwd
		self.remoteBrowseRec.append(self.pwd)
		self.downloadToRemoteFileList()

	def connect(self):
		from urlparse import urlparse
		host, ok = QtGui.QInputDialog.getText(self, 'Connect To Host', 'Host Address', QtGui.QLineEdit.Normal)
		self.host = str(host.toUtf8())
		port, ok = QtGui.QInputDialog.getText(self, 'Connect To Port', 'Port Number', QtGui.QLineEdit.Normal)
		self.port = int(port.toUtf8())
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if urlparse(self.host).hostname:
			self.host = urlparse(host).hostname
			self.sock.connect((self.host, self.port)) #connect server
		else:
			self.sock.connect((self.host, self.port)) #connect server
		self.login()

	def login(self):
		ask = loginDialog(self)
		if not ask:
			return False
		else:
			username, passwd = ask[:2]
		auth_str = "ftp_authentication|%s|%s" %(username, passwd)
		
		self.sock.send(auth_str)
		auth_feedback = self.sock.recv(1024) #wait confirm msg

		if auth_feedback == "ftp_authentication::success":
			print "Success!"
			self.username = username
			self.cur_path = username
			self.passwd = passwd
			self.initialize()
		else:
			QtGui.QMessageBox.information(self, "Error", "Wrong Username or passwd.")

	def on_remoteList_customContextMenuRequested(self, point):
		item = self.remote.fileList.itemAt(point)
		if item != None:
			self.RightItemMenuWidget()
		else:
			self.RightBlankMenuWidget()

	def on_localList_customContextMenuRequested(self, point):
		item = self.local.fileList.itemAt(point)
		if item == None:
			self.localRightBlankMenuWidget()

	def RightBlankMenuWidget(self):
		self.contextMenu = QtGui.QMenu(self)
		self.actionA = self.contextMenu.addAction("New Folder")
		self.actionA.triggered.connect(self.make_dir)
		self.contextMenu.exec_(QtGui.QCursor.pos())

	def RightItemMenuWidget(self):
		self.contextMenu = QtGui.QMenu(self)
		self.actionA = self.contextMenu.addAction("Delete")
		self.actionB = self.contextMenu.addAction("Rename")
		self.actionA.triggered.connect(self.delete)
		self.actionB.triggered.connect(self.rename)
		self.contextMenu.exec_(QtGui.QCursor.pos())

	def localRightBlankMenuWidget(self):
		self.contextMenu = QtGui.QMenu(self)
		self.actionA = self.contextMenu.addAction("New Folder")
		self.actionA.triggered.connect(self.local_make_dir)
		self.contextMenu.exec_(QtGui.QCursor.pos())

	def delete(self, msg): #delete files
		item = self.remote.fileList.currentItem()
		filename = str(item.text(0).toUtf8())
		del_str = "delete_file|%s" % filename #delete >= one file
		self.sock.send(del_str)
		feedback = self.sock.recv(1024) #wait server to confirm
		if feedback.startswith("delete::success"):
			self.updateRemoteFileList()
		elif feedback.startswith("delete::failed::unable to delete the directory or the file"):
			QtGui.QMessageBox.information(self, "Error", "Permission denied.")

	def rename(self):
		item = self.remote.fileList.currentItem()
		filename = str(item.text(0).toUtf8())
		mode = str(item.text(5).toUtf8())
		newname = nameEditDialog(self)
		if newname == False:
			return
		if newname == "":
			return
		if not mode.startswith("d"):
			if newname.split(".")[-1] != filename.split(".")[-1]:
				QtGui.QMessageBox.information(self, "Error", "Wrong file suffix.")
				return
		rm_str = "rename|%s|%s" % (filename, newname)
		self.sock.send(rm_str)
		feedback = self.sock.recv(1024) #wait server to confirm
		if feedback.startswith("rename::success"):
			self.updateRemoteFileList()
		elif feedback.startswith("rename::failed::unable to rename the file"):
			QtGui.QMessageBox.information(self, "Error", "Permission denied.")
	
	def local_make_dir(self):
		dirname = nameEditDialog(self)
		if dirname == False:
			return
		if dirname == "":
			dirname = "NewFolder"
		dirname = os.path.join(self.local_pwd, dirname)
		cmd_res = commands.getstatusoutput("mkdir %s" % dirname)[1]
		if cmd_res:
			QtGui.QMessageBox.information(self, "Error", "Folder named %s exists." %dirname)
			return
		self.updateLocalFileList()

	def make_dir(self):
		dirname = nameEditDialog(self)
		if dirname == False:
			return
		if dirname == "":
			dirname = "NewFolder"
		dir_str = "make_dir|%s" % dirname #make >= one dir
		self.sock.send(dir_str)
		feedback = self.sock.recv(1024) #wait server to confirm
		if feedback.startswith("mkdir::success"):
			self.updateRemoteFileList()
		elif feedback.startswith("mkdir::failed::unable to make directory"):
			QtGui.QMessageBox.information(self, "Error", "Permission denied.")
		elif feedback.startswith("mkdir::failed::directory exists"):
			QtGui.QMessageBox.information(self, "Error", "Folder named %s exists." %dirname)

	def downloadToRemoteFileList(self): #download file and directory list from FTP Server
		self.remote.fileList.clear()
		self.remoteWordList = []
		self.remoteDir = {}
		content = self.list_file()
		self.addItemToRemoteFileList(content)
		self.remote.completerModel.setStringList(self.remoteWordList)

	def list_file(self): #list file(s)
		instruction = "list_file|" #list >= one file
		self.sock.send(instruction)
		server_confirm_msg = self.sock.recv(100)
		content = ""
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
				content += data
		return content

	def loadToLocaFileList(self): #load file and directory list from local computer
		self.localWordList = []
		self.localDir = {}
		for f in filter( lambda x: not x.startswith("."), os.listdir(self.local_pwd)):
			pathname = os.path.join(self.local_pwd, f)
			self.addItemToLocalFileList(fileProperty(pathname))
		self.local.completerModel.setStringList(self.localWordList)

	def addItemToRemoteFileList(self, content):
		mode, num, owner, group, size, date, filename = self.parseFileInfo(content)
		for i in range(len(mode)):
			if mode[i].startswith('d'):
				icon = QtGui.QIcon(os.path.join(app_icon_path, 'folder.png'))
				pathname = os.path.join(self.pwd, filename[i])
				self.remoteDir[pathname] = True
				self.remoteWordList.append(filename[i])
			else:
				icon = QtGui.QIcon(os.path.join(app_icon_path, 'file.png'))

			item = QtGui.QTreeWidgetItem()
			item.setIcon(0, icon)
			for n, i in enumerate((filename[i].decode("utf8"), size[i], owner[i].decode("utf8"), group[i].decode("utf8"), date[i], mode[i])):
				item.setText(n, i)

			self.remote.fileList.addTopLevelItem(item)
			if not self.remote.fileList.currentItem():
				self.remote.fileList.setCurrentItem(self.remote.fileList.topLevelItem(0))
				self.remote.fileList.setEnabled(True)

	def addItemToLocalFileList(self, content):
		mode, num, owner, group, size, date, filename = self.parseFileInfo(content)
		if content.startswith('d'):
			icon = QtGui.QIcon(os.path.join(app_icon_path, 'folder.png'))
			pathname = os.path.join(self.local_pwd, filename[0])
			self.localDir[ pathname ] = True
			self.localWordList.append(filename[0])

		else:
			icon = QtGui.QIcon(os.path.join(app_icon_path, 'file.png'))

		item  = QtGui.QTreeWidgetItem( )
		item.setIcon(0, icon)
		for n, i in enumerate((filename[0].decode("utf8"), size[0], owner[0].decode("utf8"), group[0].decode("utf8"), date[0], mode[0])):
			item.setText(n, i)
		self.local.fileList.addTopLevelItem(item)
		if not self.local.fileList.currentItem():
			self.local.fileList.setCurrentItem(self.local.fileList.topLevelItem(0))
			self.local.fileList.setEnabled(True)

	def parseFileInfo(self, file):
		"""
		parse files information "drwxr-xr-x 2 root wheel 1024 Nov 17 1993 lib" result like follower
		                        "drwxr-xr-x", "2", "root", "wheel", "1024 Nov 17 1993", "lib"
		"""
		file = re.sub("total .*\n", "", file)
		file = [f for f in file.split('\n') if f != '']
		(mode, num, owner, group, size, date, filename) = ([], [], [], [], [], [], [])
		for i in file:
			item = [f for f in i.split(' ') if f != '']
			mode.append(item[0])
			num.append(item[1])
			owner.append(item[2])
			group.append(item[3])
			size.append(item[4])
			date.append(' '.join(item[5:8]))
			filename.append(' '.join(item[8:]))
		return (mode, num, owner, group, size, date, filename)

	def cdToRemotePath(self):
		pathname = str(self.remote.pathEdit.text().toUtf8())
		try:
			self.switch_dir("cd %s" % pathname)
			if self.feedback == "Error":
				QtGui.QMessageBox.information(self, "Error", "Invalid directory name.")
				return
		except:
			return
		self.cwd = pathname.startswith(os.path.sep) and pathname or os.path.join(self.pwd, pathname)
		self.updateRemoteFileList()
		self.remote.backButton.setEnabled(True)
		self.remoteBrowseRec.append(self.pwd)
		if os.path.abspath(pathname) != self.remoteOriginPath:
			self.remote.homeButton.setEnabled(True)
		else:
			self.remote.homeButton.setEnabled(False)

	def cdToRemoteDirectory(self, item, column):
		pathname = os.path.join(self.pwd, str(item.text(0)))
		if not self.isRemoteDir(pathname):
			return
		while self.remoteBackCount > 0:
			if len(self.remoteBrowseRec) == 1:
				break
			del self.remoteBrowseRec[-1]
			self.remoteBackCount -= 1

		self.remoteBrowseRec.append(pathname)
		if self.pwd:
			nextdir = pathname.split(self.pwd + os.path.sep)
		else:
			nextdir = ["", pathname]
		self.switch_dir("cd %s" % nextdir[1])
		self.updateRemoteFileList()
		self.remote.backButton.setEnabled(True)
		if pathname != self.remoteOriginPath:
			self.remote.homeButton.setEnabled(True)

	def cdToRemoteBackDirectory(self):
		pathname = self.remoteBrowseRec[self.remoteBrowseRec.index(self.pwd)-1 ]
		self.remoteBackCount += 1
		if pathname != self.remoteBrowseRec[0]:
			self.remote.backButton.setEnabled(True)
		else:
			self.remote.backButton.setEnabled(False)

		if pathname != self.remoteOriginPath:
			self.remote.homeButton.setEnabled(True)
		else:
			self.remote.homeButton.setEnabled(False)
		self.remote.nextButton.setEnabled(True)
		self.cwdDetermined(pathname)
		self.switch_dir("cd %s" % self.cwd)
		self.updateRemoteFileList()

	def cwdDetermined(self, pathname):
		if pathname.startswith(self.pwd):
			tmp = pathname.split(self.pwd + os.path.sep)
			self.cwd = tmp[1]
		elif self.pwd.startswith(pathname):
			tmp = self.pwd.split(pathname + os.path.sep)
			tmp = tmp[1].split(os.path.sep)
			for i in range(len(tmp)):
				tmp[i] = ".."
			self.cwd = "/".join(tmp)
		self.pwd = pathname

	def cdToRemoteNextDirectory(self):
		if ((self.remoteBrowseRec.index(self.pwd)+1) >= len(self.remoteBrowseRec)):
			self.remote.nextButton.setEnabled(False)
			return

		pathname = self.remoteBrowseRec[self.remoteBrowseRec.index(self.pwd)+1]
		if pathname != self.remoteBrowseRec[-1]:
			self.remote.nextButton.setEnabled(True)
		else:
			self.remote.nextButton.setEnabled(False)
		self.remote.backButton.setEnabled(True)
		if pathname != self.remoteOriginPath:
			self.remote.homeButton.setEnabled(True)
		else:
			self.remote.homeButton.setEnabled(False)
		self.remote.backButton.setEnabled(True)
		self.cwdDetermined(pathname)
		self.pwd = pathname
		self.switch_dir("cd %s" % self.cwd)
		self.updateRemoteFileList()

	def switch_dir(self, msg): #switch directory
		msg = msg.split()
		self.sock.send("switch_dir|%s" % " ".join(msg)) #one | more than one msg
		feedback = self.sock.recv(100)

		if feedback.startswith("switch_dir::ok"):
			self.pwd = feedback.split("::")[-1] #result
			self.pwd = self.remoteOriginPath + self.pwd
			self.feedback = "Right"
		elif feedback.startswith("switch_dir::error::target dir doesn't exist"):
			self.feedback = "Error"

	def cdToRemoteHomeDirectory(self):
		self.switch_dir("cd")
		self.remoteBrowseRec.append(self.remoteOriginPath)
		self.updateRemoteFileList()
		self.remote.homeButton.setEnabled(False)

	def updateRemoteFileList(self):
		self.downloadToRemoteFileList()

	def isRemoteDir(self, dirname):
		return self.remoteDir.get(dirname, None)

	def download(self):
		self.progressDialog = ProgressDialog(self)
		item = self.remote.fileList.currentItem()
		filename = str(item.text(0).toUtf8())
		srcfile  = os.path.join(self.pwd, str(item.text(0).toUtf8()))
		filesize = int(item.text(1))
		dstfile  = os.path.join(self.local_pwd, str(item.text(0).toUtf8()))
		pb = DownloadProgressWidget(text=srcfile)
		pb.set_max(filesize)
		self.progressDialog.addProgressbar(pb)
		self.progressDialog.show()

		get_str = "file_transfer|get|%s" % filename
		self.sock.send(get_str)
		feedback = self.sock.recv(1024) #wait server to confirm
		
		if feedback.startswith("file_transfer::get_file::send_ready"): #server is ready to send file
			file = open(dstfile, 'wb')
			self.sock.send(("file_transfer::get_file::recv_ready")) #tell server that client is ready
			recvsize = 0
			
			if filesize == 0:
				pb.set_value(" ")

			while not filesize == recvsize:
				data = self.sock.recv(filesize - recvsize) #1024 bytes every time
				recvsize += len(data)
				pb.set_value(data)
				file.write(data)
			file.close()
		elif feedback.startswith("file_transfer::get_file::error::unable to download the file"):
			QtGui.QMessageBox.information(self, "Error", "Permission denied.")
		self.updateLocalFileList()


	def upload(self):
		self.progressDialog = ProgressDialog(self)
		item = self.local.fileList.currentItem()
		filename = str(item.text(0).toUtf8())
		srcfile  = os.path.join(self.local_pwd, filename)
		filesize = int(item.text(1))
		dstfile  = os.path.join(self.pwd, str(item.text(0).toUtf8()))

		pb = UploadProgressWidget(text=srcfile)
		pb.set_max(filesize)
		self.progressDialog.addProgressbar(pb)
		self.progressDialog.show()
		
		put_str = "file_transfer|put|send_ready|%s|%s" %(filename, filesize)
		self.sock.send(put_str)
		feedback = self.sock.recv(1024)
		
		if feedback.startswith("file_transfer::put_file::recv_ready"):
			file = open(srcfile, 'rb')
			sentsize = 0

			while not sentsize == filesize: #send 1024 bytes once a time
				if filesize - sentsize <= 1024: 
					num = filesize -sentsize
					data = file.read(filesize - sentsize)
					sentsize += (filesize - sentsize)
				else:
					data = file.read(1024)
					sentsize += 1024
				self.sock.send(data)
				pb.set_value(data)
			file.close()
		elif feedback.startswith("file_transfer::put_file::unable to upload the file"):
			QtGui.QMessageBox.information(self, "Error", "Permission denied.")
		self.updateRemoteFileList()

	def cdToLocalPath(self):
		pathname = str(self.local.pathEdit.text().toUtf8())
		pathname = pathname.endswith(os.path.sep) and pathname or os.path.join(self.local_pwd, pathname)
		if not os.path.exists(pathname) and not os.path.isdir(pathname):
			return

		else:
			self.localBrowseRec.append(pathname)
			self.local_pwd = pathname
			self.updateLocalFileList()
			self.local.backButton.setEnabled(True)
			if os.path.abspath(pathname) != self.localOriginPath:
				self.local.homeButton.setEnabled(True)
			else:
				self.local.homeButton.setEnabled(False)

	def cdToLocalDirectory(self, item, column):
		pathname = os.path.join(self.local_pwd, str(item.text(0)))
		if not self.isLocalDir(pathname):
			return
		while self.localBackCount > 0:
			if len(self.localBrowseRec) == 1:
				break
			del self.localBrowseRec[-1]
			self.localBackCount -= 1
		self.localBrowseRec.append(pathname)
		self.local_pwd = pathname
		self.updateLocalFileList()
		self.local.backButton.setEnabled(True)
		if pathname != self.localOriginPath:
			self.local.homeButton.setEnabled(True)

	def cdToLocalBackDirectory(self):
		pathname = self.localBrowseRec[ self.localBrowseRec.index(self.local_pwd)-1 ]
		self.localBackCount += 1
		if pathname != self.localBrowseRec[0]:
			self.local.backButton.setEnabled(True)
		else:
			self.local.backButton.setEnabled(False)
		if pathname != self.localOriginPath:
			self.local.homeButton.setEnabled(True)
		else:
			self.local.homeButton.setEnabled(False)
		self.local.nextButton.setEnabled(True)
		self.local_pwd = pathname
		self.updateLocalFileList()

	def cdToLocalNextDirectory(self):
		if ((self.localBrowseRec.index(self.local_pwd)+1) >= len(self.localBrowseRec)):
			self.local.nextButton.setEnabled(False)
			return
		pathname = self.localBrowseRec[self.localBrowseRec.index(self.local_pwd)+1]
		if pathname != self.localBrowseRec[-1]:
			self.local.nextButton.setEnabled(True)
		else:
			self.local.nextButton.setEnabled(False)
		if pathname != self.localOriginPath:
			self.local.homeButton.setEnabled(True)
		else:
			self.local.homeButton.setEnabled(False)
		self.local.backButton.setEnabled(True)
		self.local_pwd = pathname
		self.updateLocalFileList()

	def cdToLocalHomeDirectory(self):
		self.local_pwd = self.localOriginPath
		self.updateLocalFileList()
		self.local.homeButton.setEnabled(False)

	def updateLocalFileList(self):
		self.local.fileList.clear()
		self.loadToLocaFileList()

	def isLocalDir(self, dirname):
		return self.localDir.get(dirname, None)


if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	client = FtpClient()
	client.show()
	app.exec_()