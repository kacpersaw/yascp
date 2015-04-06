
import ScreenCloud, uuid, paramiko, datetime, os
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
		self.username = settings.value("username", "")
		self.password = settings.value("password", "")
		self.host = settings.value("host", "")
		self.port = int(settings.value("port", 22))
		self.url = settings.value("url", "")
		self.path = settings.value("path", "")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("yascp")
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
		return not(not self.username or not self.password or not self.host or not self.port or not self.url or not self.path)

	def getFilename(self):
		self.loadSettings()
		name = uuid.uuid4().hex
		return ScreenCloud.formatFilename(name[:16])

	def upload(self, screenshot, name):
		self.loadSettings()
		f = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(name)
		screenshot.save(QFile(f), ScreenCloud.getScreenshotFormat())

		now = datetime.datetime.now()
		date = "/%s/%s/%s" % (now.year, now.month, now.day)
		path = "/%s/%s/%s/%s" % (now.year, now.month, now.day, ScreenCloud.formatFilename(name))

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
		
		url = "%s%s/%s/%s/%s" % (self.url, now.year, now.month, now.day, ScreenCloud.formatFilename(name))
		ScreenCloud.setUrl(self.url.strip("/") + path)

		return True
