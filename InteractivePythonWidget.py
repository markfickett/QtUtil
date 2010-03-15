__all__ = [
	'InteractivePythonWidget',
]

from Manifest import QtCore, QtGui, \
	code, sys, traceback, rlcompleter, os, enum, \
	logging
import Drawing, Settings

log = logging.getLogger('InteractivePythonWidget')



# http://docs.python.org/library/code.html
class InteractivePythonWidget(QtGui.QWidget, code.InteractiveInterpreter):
	"""
	Execute Python and show the results of execution.
	"""
	TAB_WIDTH = 4
	TB_HEADER = 'Traceback (most recent call last):'
	STYLE = enum.Enum('OUTPUT', 'CONTEXT', 'ERROR')
	SETTINGS_GROUP_NAME = 'InteractivePythonWidget'
	SETTINGS_NAME_SPLITTER = 'splitter'
	SETTINGS_NAME_GEOMETRY = 'windowGeometry'
	def __init__(self, parent=None, locals={}):
		QtGui.QWidget.__init__(self, parent)

		self.__errRedirect = StdRedirect(sys.stderr, self.writeStderr)
		self.__outRedirect = StdRedirect(sys.stdout, self.writeStdout)
		sys.stderr = self.__errRedirect
		sys.stdout = self.__outRedirect
		self.__errorOccurred = False

		code.InteractiveInterpreter.__init__(self, locals)

		f = QtGui.QFont()
		f.setFixedPitch(True)
		f.setFamily('Monaco')
		f.setPointSize(10)
		self.setFont(f)

		layout = QtGui.QVBoxLayout(self)
		layout.setSpacing(0)
		layout.setMargin(QtGui.QApplication.style()
			.pixelMetric(QtGui.QStyle.PM_SplitterWidth))

		self.__splitter = QtGui.QSplitter(QtCore.Qt.Vertical, self)
		layout.addWidget(self.__splitter)

		tabWidth = self.TAB_WIDTH*self.fontMetrics().averageCharWidth()
		self.__outputField = QtGui.QTextEdit(self.__splitter)
		self.__outputField.setReadOnly(True)
		self.__outputField.setTabStopWidth(tabWidth)
		self.__splitter.addWidget(self.__outputField)

		self.__inputField = PythonInputWidget(self, locals)
		self.__inputField.setAcceptRichText(False)
		self.__inputField.setTabChangesFocus(False)
		self.__inputField.setTabStopWidth(tabWidth)
		self.__splitter.addWidget(self.__inputField)

		QtCore.QObject.connect(self.__inputField,
			QtCore.SIGNAL('execute'), self.__execute)
		QtCore.QObject.connect(self.__inputField,
			QtCore.SIGNAL('completions'), self.__showCompletions)


	def __execute(self, sourceText):
		with self.__errRedirect:
			with self.__outRedirect:
				self.__errorOccurred = False
				self.__runSourceGradually(sourceText)

		if not self.__errorOccurred:
			self.__inputField.executionComplete()


	def __runSourceGradually(self, sourceText):
		lines = sourceText.split('\n')
		buffer = ''
		for line in lines:
			if buffer:
				prompt = sys.ps2
			else:
				prompt = sys.ps1
			self.__appendOutputText('%s%s\n' % (prompt,  line),
				self.STYLE.CONTEXT)

			buffer += '\n' + line
			if not self.runsource(buffer):
				buffer = ''
			if self.__errorOccurred:
				break
		if buffer:
			# Catch (for example) function definitions without
			#	a trailing newline.
			buffer += '\n'
			if self.runsource(buffer):
				self.__errorOccurred = True
				self.__appendOutputText('Input incomplete.',
					self.STYLE.ERROR)


	def write(self, outputText):
		"""Undifferentiated writing (not used)."""
		self.__appendOutputText('unexpected write: ' + outputText,
			self.STYLE.ERROR)


	def __showInputError(self):
		"""
		Print a SyntaxError or ValueError from compiling user code.
		"""
		excClass, excObj, tb = sys.exc_info()
		formattedExcList = traceback.format_exception_only(
			excClass, excObj)
		for formattedExcLine in formattedExcList:
			self.__appendOutputText(formattedExcLine,
				self.STYLE.ERROR)


	def showsyntaxerror(self, filename=None):
		self.__errorOccurred = True
		self.__showInputError()


	def showtraceback(self):
		"""
		Print a traceback from executing user code.
		"""
		self.__errorOccurred = True
		excClass, excObj, tb = sys.exc_info()

		formattedTbList = traceback.format_tb(tb)
		formattedExcList = traceback.format_exception_only(
			excClass, excObj)

		self.__appendOutputText(self.TB_HEADER, self.STYLE.ERROR)
		self.__appendOutputText('\n'.join(formattedTbList[1:]),
			self.STYLE.ERROR)
		for formattedExcLine in formattedExcList:
			self.__appendOutputText(formattedExcLine,
				self.STYLE.ERROR)


	def writeStdout(self, outputText):
		"""Print output sent to stdout from user code."""
		self.__appendOutputText(outputText, self.STYLE.OUTPUT)


	def writeStderr(self, outputText):
		"""Print output sent to stderr from user code."""
		self.__appendOutputText(outputText, self.STYLE.ERROR)


	def __showCompletions(self, completionList):
		self.__appendOutputText('%s\n' % completionList,
			self.STYLE.CONTEXT)


	def __appendOutputText(self, text, style):

		format = QtGui.QTextCharFormat()
		if style == self.STYLE.OUTPUT:
			color = self.palette().color(QtGui.QPalette.Text)
		elif style == self.STYLE.CONTEXT:
			color = self.palette().color(QtGui.QPalette.Disabled,
				QtGui.QPalette.Text)
		elif style == self.STYLE.ERROR:
			color = Drawing.GetErrorColor()
		format.setForeground(QtGui.QBrush(color))

		self.__outputField.moveCursor(QtGui.QTextCursor.End)
		self.__outputField.textCursor().insertText(text, format)


	def writeSettings(self, settings):
		with Settings.GroupGuard(settings, self.SETTINGS_GROUP_NAME):
			Settings.WriteWidgetGeometry(settings,
				self.SETTINGS_NAME_GEOMETRY, self)
			settings.setValue(self.SETTINGS_NAME_SPLITTER,
				QtCore.QVariant(self.__splitter.saveState()))
			self.__inputField.writeSettings(settings)


	def readSettings(self, settings):
		with Settings.GroupGuard(settings, self.SETTINGS_GROUP_NAME):
			Settings.ReadWidgetGeometry(settings,
				self.SETTINGS_NAME_GEOMETRY, self)
			splitterSettings = settings.value(
				self.SETTINGS_NAME_SPLITTER).toByteArray()
			if not splitterSettings.isNull():
				self.__splitter.restoreState(splitterSettings)
			self.__inputField.readSettings(settings)



class StdRedirect(object):
	"""
	When in context, redirect output to the given callback.
	"""
	def __init__(self, orig, cb):
		self.__orig = orig
		self.__cb = cb
		self.__enabled = False


	def write(self, s):
		if self.__enabled:
			self.__cb(s)
		else:
			self.__orig.write(s)


	def __enter__(self):
		self.__enabled = True


	def __exit__(self, excType, excValue, tb):
		self.__enabled = False



class PythonInputWidget(QtGui.QTextEdit):
	"""
	Signals:
		execute		text (Python code to execute)
		completions	list of possible completions
	"""
	SETTINGS_GROUP_NAME = 'PythonInputWidget'
	SETTINGS_NAME_HISTORY = 'history'
	SETTINGS_NAME_HISTORY_ENTRY = 'entry'
	MAX_SAVED_HISTORY = 1023
	def __init__(self, parent, locals):
		QtGui.QTextEdit.__init__(self, parent)
		self.__commandHistory = []
		self.__commandHistoryIndex = None
		self.__swapText = None

		self.__completer = rlcompleter.Completer()
		self.__completer.use_main_ns = False
		self.__completer.namespace = locals


	def keyPressEvent(self, event):
		k = event.key()
		mods = event.modifiers()

		if ((k == QtCore.Qt.Key_Enter) or (k == QtCore.Qt.Key_Return
		and mods & (QtCore.Qt.ControlModifier|QtCore.Qt.MetaModifier))
		and not event.isAutoRepeat()):
			self.__execute()
			return
		elif (k == QtCore.Qt.Key_Tab and not event.isAutoRepeat()
		and self.__shouldAutoComplete()):
			self.__autoComplete()
			return
		elif k in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
			if (event.modifiers()
			& (QtCore.Qt.AltModifier|QtCore.Qt.MetaModifier) ):
				self.__showHistory(k == QtCore.Qt.Key_Up)
			else:
				self.__moveCursorVertical(event)
			return
		elif ((k == QtCore.Qt.Key_U) and (mods
		& (QtCore.Qt.ControlModifier|QtCore.Qt.MetaModifier))):
			self.__clearCurrentLineOrDocument()
			return

		return QtGui.QTextEdit.keyPressEvent(self, event)


	def __getPlainText(self, selectionOnly=False, cursor=None):
		if selectionOnly:
			# Selection doesn't do a to-plain conversion, so (for
			# example) paragraph-separator u'\u2029' doesn't get
			# converted to '\n' as it does from .toPlainText().
			c = cursor or self.textCursor()
			qstr = c.selectedText()
			try:
				return str(qstr)
			except UnicodeEncodeError:
				doc = QtGui.QTextDocument(qstr)
				qstr = doc.toPlainText()
				return str(qstr)
		else:
			return str(self.toPlainText())


	def __moveCursorVertical(self, event):
		oldPos = self.textCursor().position()
		QtGui.QTextEdit.keyPressEvent(self, event)

		if self.textCursor().position() == oldPos:
			if event.key() == QtCore.Qt.Key_Up:
				self.moveCursor(QtGui.QTextCursor.StartOfLine)
			else:
				self.moveCursor(QtGui.QTextCursor.EndOfLine)


	def __clearCurrentLineOrDocument(self):
		doc = self.document()
		cursor = QtGui.QTextCursor(doc)
		cursor.setPosition(self.textCursor().position())
		cursor.movePosition(QtGui.QTextCursor.EndOfLine)
		cursor.movePosition(QtGui.QTextCursor.StartOfLine,
			QtGui.QTextCursor.KeepAnchor)
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.Document)
		cursor.removeSelectedText()


	def executionComplete(self):
		"""
		Execution has completed successfully.
		Store history and clear as appropriate.
		"""
		allText = self.__getPlainText()
		if not self.textCursor().hasSelection():
			self.clear()

		self.__commandHistory.append(allText)
		self.__commandHistoryIndex = None


	def __execute(self):
		text = self.__getPlainText(
			selectionOnly=self.textCursor().hasSelection())
		if not text:
			return

		self.emit(QtCore.SIGNAL('execute'), text)


	def __shouldAutoComplete(self):
		"""
		Don't auto-complete if there's a selection,
		or if the cursor is positioned after whitespace.
		"""
		cursor = self.textCursor()
		if cursor.hasSelection():
			return False

		# The character at cursor.position() is the one after it.
		doc = self.document()
		c = doc.characterAt(cursor.position()-1)
		return self.__isPythonIdentifier(c)


	def __isPythonIdentifier(self, qChar):
		return qChar.isLetterOrNumber() or qChar.toAscii() == '.'


	def __autoComplete(self):
		doc = self.document()
		cursor = QtGui.QTextCursor(doc)
		cursor.setPosition(self.textCursor().position())

		leftPos = rightPos = cursor.position()-1
		c = doc.characterAt(rightPos)
		while self.__isPythonIdentifier(c):
			rightPos += 1
			cursor.movePosition(QtGui.QTextCursor.NextCharacter)
			c = doc.characterAt(rightPos)
		rightPos += 1
		c = doc.characterAt(leftPos)
		while self.__isPythonIdentifier(c):
			leftPos -= 1
			c = doc.characterAt(leftPos)
		leftPos += 1

		cursor.movePosition(QtGui.QTextCursor.PreviousCharacter,
			QtGui.QTextCursor.KeepAnchor, (rightPos-leftPos) - 1)

		text = self.__getPlainText(cursor=cursor, selectionOnly=True)

		completions = []
		i = 0
		completion = self.__completer.complete(text, i)
		while completion is not None:
			completions.append(completion)
			i += 1
			completion = self.__completer.complete(text, i)

		replacement = None
		if not completions:
			return
		elif len(completions) > 1:
			self.emit(QtCore.SIGNAL('completions'), completions)
			replacement = os.path.commonprefix(completions)
		else:
			replacement = completions[0]

		if replacement:
			cursor.removeSelectedText()
			cursor.insertText(replacement)


	def __showHistory(self, older):
		if not self.__commandHistory:
			return

		currentText = self.__getPlainText()

		i = oldIndex = self.__commandHistoryIndex
		n = len(self.__commandHistory)
		if i is None:
			if older:
				i = -1
			else:
				return
		else:
			if older and abs(i) < n:
				i -= 1
			elif (not older) and i < 0:
				i += 1
			else:
				return

		if i == 0:
			self.__commandHistoryIndex = None
			if self.__swapText:
				self.setPlainText(self.__swapText)
				self.__swapText = None
			else:
				self.clear()
		else:
			if oldIndex is None:
				self.__swapText = currentText
			self.setPlainText(self.__commandHistory[i])
			self.__commandHistoryIndex = i
		self.moveCursor(QtGui.QTextCursor.End)


	def readSettings(self, settings):
		with Settings.GroupGuard(settings, self.SETTINGS_GROUP_NAME):
			with Settings.ArrayReadGuard(settings,
			self.SETTINGS_NAME_HISTORY) as n:
				for i in xrange(n):
					self.__readHistorySetting(settings, i)


	def __readHistorySetting(self, settings, i):
		settings.setArrayIndex(i)
		qv = settings.value(self.SETTINGS_NAME_HISTORY_ENTRY)
		qstr = qv.toString()
		if not qstr.isNull():
			self.__commandHistory.append(str(qstr))


	def writeSettings(self, settings):
		with Settings.GroupGuard(settings, self.SETTINGS_GROUP_NAME):
			with Settings.ArrayWriteGuard(settings,
			self.SETTINGS_NAME_HISTORY):
				history = self.__commandHistory[
					-self.MAX_SAVED_HISTORY:]
				for i, h in enumerate(history):
					self.__writeHistorySetting(
						settings, i, h)


	def __writeHistorySetting(self, settings, i, historyEntry):
		settings.setArrayIndex(i)
		settings.setValue(self.SETTINGS_NAME_HISTORY_ENTRY,
			QtCore.QVariant(QtCore.QVariant(historyEntry)))



