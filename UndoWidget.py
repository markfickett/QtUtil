from Manifest import QtGui, QtCore, logging
import Util
log = logging.getLogger('UndoWidget')

__all__ = [
	'UndoWidget',
]



class UndoWidget(QtGui.QWidget):
	"""
	Display undo events and supply undo-related controls.
	"""
	__UNDO_FLAGS = QtCore.Qt.ItemIsEnabled
	__REDO_FLAGS = QtCore.Qt.NoItemFlags
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		layout = QtGui.QVBoxLayout(self)

		self.__list = QtGui.QListWidget(self)
		self.__list.setFocusPolicy(QtCore.Qt.NoFocus)
		layout.addWidget(self.__list)

		undoNames, redoNames = Util.Undo.GetEntryNames()
		i = None
		for u in undoNames:
			i = QtGui.QListWidgetItem(u, self.__list)
			i.setFlags(self.__UNDO_FLAGS)

		if i is not None:
			self.__lastDoneRow = self.__list.row(i)
		else:
			self.__lastDoneRow = -1

		for r in redoNames:
			i = QtGui.QListWidgetItem(r, self.__list)
			i.setFlags(self.__REDO_FLAGS)

		buttonLayout = QtGui.QHBoxLayout()
		layout.addLayout(buttonLayout)

		buttonLayout.addStretch()

		self.__undoButton = QtGui.QPushButton('Undo', self)
		QtCore.QObject.connect(self.__undoButton,
			QtCore.SIGNAL('clicked()'), Util.Undo.Undo)
		buttonLayout.addWidget(self.__undoButton)

		self.__redoButton = QtGui.QPushButton('Redo', self)
		QtCore.QObject.connect(self.__redoButton,
			QtCore.SIGNAL('clicked()'), Util.Undo.Redo)
		buttonLayout.addWidget(self.__redoButton)

		Util.Events.RegisterEventHandler(self.__undone,
			eventType=Util.Undo.EVENT_UNDONE)
		Util.Events.RegisterEventHandler(self.__redone,
			eventType=Util.Undo.EVENT_REDONE)
		Util.Events.RegisterEventHandler(self.__undoEntryAppended,
			eventType=Util.Undo.EVENT_APPENDED)
		Util.Events.RegisterEventHandler(self.__undoGroupClosed,
			eventType=Util.Undo.EVENT_GROUP_CLOSED)

		self.__updateButtons()


	def __updateButtons(self):
		self.__undoButton.setEnabled(self.__lastDoneRow >= 0)
		lastIndex = self.__list.count() - 1
		self.__redoButton.setEnabled(lastIndex > self.__lastDoneRow
			and lastIndex >= 0 )


	def __undoEntryAppended(self, eventType, eventID,
		name=None, inGroup=False):

		if inGroup:
			return

		redoIndices = range(self.__lastDoneRow+1, self.__list.count())
		for i in reversed(redoIndices):
			self.__list.takeItem(i)

		item = QtGui.QListWidgetItem(name or '', self.__list)
		item.setFlags(self.__UNDO_FLAGS)
		self.__lastDoneRow += 1
		self.__updateButtons()


	def __undoGroupClosed(self, eventType, eventID, name=None):
		if name is not None:
			item = self.__list.item(self.__lastDoneRow)
			item.setText(name)


	def __undone(self, eventType, eventID):
		item = self.__list.item(self.__lastDoneRow)
		self.__lastDoneRow -= 1
		item.setFlags(item.flags() & (~QtCore.Qt.ItemIsEnabled))
		self.__updateButtons()


	def __redone(self, eventType, eventID):
		self.__lastDoneRow += 1
		item = self.__list.item(self.__lastDoneRow)
		item.setFlags(item.flags() | QtCore.Qt.ItemIsEnabled)
		self.__updateButtons()



