
import ScreenCloud, uuid, paramiko, datetime, os, ftplib
from PythonQt.QtCore import QFile, QSettings, QIODevice
from PythonQt.QtGui import QWidget, QDialog, QFileDialog, QMessageBox, QDesktopServices
from PythonQt.QtUiTools import QUiLoader

class YASCPUploader():
	def __init__(self):
		self.uil = QUiLoader()
		self.loadSettings()

	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.settingsDialog.group_server.combo_type.setCurrentIndex(self.settingsDialog.group_server.combo_type.findText(self.type))
		self.settingsDialog.group_server.input_username.text = self.username
		self.settingsDialog.group_server.input_password.text = self.password
		self.settingsDialog.group_server.input_host.text = self.host
		self.settingsDialog.group_server.input_port.text = self.port
		self.settingsDialog.group_upload.input_url.text = self.url
		self.settingsDialog.group_upload.input_path.text = self.path
		self.settingsDialog.open()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("yascp")
		self.type = settings.value("type", "SFTP")
		self.username = settings.value("username", "")
		self.password = settings.value("password", "")
		self.host = settings.value("host", "")

		if self.type == "FTP":
			port = 21
		elif self.type == "SFTP":
			port = 22

		self.port = int(settings.value("port", port))
		self.url = settings.value("url", "")
		self.path = settings.value("path", "")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("yascp")
		settings.setValue("type", self.settingsDialog.group_server.combo_type.currentText)
		settings.setValue("username", self.settingsDialog.group_server.input_username.text)
		settings.setValue("password", self.settingsDialog.group_server.input_password.text)
		settings.setValue("host", self.settingsDialog.group_server.input_host.text)
		settings.setValue("port", self.settingsDialog.group_server.input_port.text)
		settings.setValue("url", self.settingsDialog.group_upload.input_url.text)
		settings.setValue("path", self.settingsDialog.group_upload.input_path.text)
		settings.endGroup()
		settings.endGroup()

	def isConfigured(self):
		self.loadSettings()
		return not(not self.username or not self.password or not self.host or not self.port or not self.url or not self.path or not self.type)

	def getFilename(self):
		self.loadSettings()
		name = uuid.uuid4().hex
		return ScreenCloud.formatFilename(name[:16])

	def upload(self, screenshot, name):
		self.loadSettings()
		f = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(name)
		screenshot.save(QFile(f), ScreenCloud.getScreenshotFormat())

		now = datetime.datetime.now()
		date = "/%s/%02d/%02d" % (now.year, now.month, now.day)
		path = "/%s/%02d/%02d/%s" % (now.year, now.month, now.day, ScreenCloud.formatFilename(name))

		if self.type == "SFTP":
			transport = paramiko.Transport((self.host, self.port))
			transport.connect(username = self.username, password = self.password)

			sftp = paramiko.SFTPClient.from_transport(transport)
			try:
				sftp.chdir(os.path.normpath(self.path) + date)
			except IOError:
				sftp.mkdir(os.path.normpath(self.path) + date)

			try:
				sftp.put(f, os.path.normpath(self.path) + path)
			except IOError:
				ScreenCloud.setError("Failed to write file")
			
			sftp.close()
			transport.close()
		elif self.type == "FTP":
			ftp = ftplib.FTP()
			ftp.connect(self.host, self.port)
			ftp.login(self.username, self.password)
			
			if os.path.normpath(self.path) in ftp.nlst():
				try:
					ftp.cwd(os.path.normpath(self.path))
				except ftplib.error_perm as err:
					ScreenCloud.setError(err.message)
					return False

			year = "%02d" % now.year
			month = "%02d" % now.month
			day = "%02d" % now.day

			if year in ftp.nlst():
				ftp.cwd(year)
			else:
				ftp.mkd(year)
				ftp.cwd(year)

			if month in ftp.nlst():
				ftp.cwd(month)
			else:
				ftp.mkd(month)
				ftp.cwd(month)

			if day in ftp.nlst():
				ftp.cwd(day)
			else:
				ftp.mkd(day)
				ftp.cwd(day)

			#borrowed from screencloud ftp plugin
			fs = open(f, 'rb')
			try:
				ftp.storbinary('STOR ' + name, fs)
			except ftplib.error_perm as err:
				ScreenCloud.setError(err.message)
				return False

			ftp.quit()
			fs.close()

		url = "%s%s/%s/%s/%s" % (self.url, now.year, now.month, now.day, ScreenCloud.formatFilename(name))
		ScreenCloud.setUrl(self.url.strip("/") + path)

		return True
