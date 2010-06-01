__all__ = [
	'DateEditor',
]

from UI.Manifest import QtCore, QtGui, datetime, logging
import DataModel, Util
log = logging.getLogger('DateEditor')



class DateEditor(QtGui.QWidget):
	"""
	Edit DataModel.Date. Provide a free-form text editing field,
	and a label which shows how the text has been parsed.
	"""
	__UNKNOWN = '?'
	__MONTH_NAMES = tuple([
		datetime.date(1900, m, 1).strftime('%b') for m in xrange(1, 13)
	])
	__MONTH_NAMES_LOWER = tuple([m.lower() for m in __MONTH_NAMES])
	def __init__(self, date, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.__date = date

		layout = QtGui.QHBoxLayout(self)

		self.__nameLabel = QtGui.QLabel(self)
		layout.addWidget(self.__nameLabel)

		self.__field = QtGui.QLineEdit(self)
		layout.addWidget(self.__field)

		self.__label = QtGui.QLabel(self)
		layout.addWidget(self.__label)

		self.__updateForChanges = True

		eventHandlers = (
			(self.__nameChanged, DataModel.Date.EVENT_SET_NAME),
			(self.__dayChanged, DataModel.Date.EVENT_SET_DAY),
			(self.__monthChanged, DataModel.Date.EVENT_SET_MONTH),
			(self.__yearChanged, DataModel.Date.EVENT_SET_YEAR),
		)

		for handler, eventType in eventHandlers:
			Util.Events.RegisterEventHandler(handler, eventID=date,
				eventType=eventType)
			handler(eventType, date)

		QtCore.QObject.connect(self.__field,
			QtCore.SIGNAL('textEdited(const QString&)'),
			self.__fieldEdited)

		QtCore.QObject.connect(self.__field,
			QtCore.SIGNAL('editingFinished()'),
			self.__editingFinished)


	def __nameChanged(self, type, date, oldName=None, newName=None):
		self.__nameLabel.setText(date.getName())


	def __dayChanged(self, type, date, oldDay=None, newDay=None):
		if self.__updateForChanges:
			self.__updateLabel()
			self.__updateField()


	def __monthChanged(self, type, date, oldMonth=None, newMonth=None):
		if self.__updateForChanges:
			self.__updateLabel()
			self.__updateField()


	def __yearChanged(self, type, date, oldYear=None, newYear=None):
		if self.__updateForChanges:
			self.__updateLabel()
			self.__updateField()


	def __parse(self, text):
		"""
		Parse the given text into a Date object as forgivingly
		as possible. Return the Date object, or None if parsing fails.
		"""
		parts = text.replace('-', ' ').replace('/', ' ').split()
		date = DataModel.Date()
		if not parts:
			return date
		numParts = []
		strParts = []
		for p in parts:
			if p.isdigit():
				try:
					n = int(p)
					numParts.append(n)
				except ValueError:
					return None
			elif p.isalpha():
				strParts.append(p)
			elif p == self.__UNKNOWN:
				numParts.append(None)
			else:
				return None

		if len(strParts) > 1:
			return None
		elif len(strParts) == 1:
			s = strParts[0].lower()
			for i, m in enumerate(self.__MONTH_NAMES_LOWER):
				if m.startswith(s):
					date.setMonth(i+1)
					break
			if not date.hasMonth():
				return None

		if len(numParts) == 3 and date.hasMonth():
			return None
		if len(numParts) > 3:
			return None

		needDay = True
		needYear = True
		needMonth = not date.hasMonth()
		while numParts:
			n = numParts.pop()
			if needDay and \
			(n is None or DataModel.Date.CheckDay(n)):
				if n is not None:
					date.setDay(n)
				needDay = False
			elif needMonth and \
			(n is None or DataModel.Date.CheckMonth(n)):
				if n is not None:
					date.setMonth(n)
				needMonth = False
			elif needYear:
				if n is not None:
					date.setYear(n)
				needYear = False
			else:
				return None

		return date


	def __format(self, date):
		"""
		Format the given Date object as a string.
		"""
		if not (date.hasYear() or date.hasMonth() or date.hasDay()):
			return ''

		dateStrParts = []

		if date.hasYear():
			dateStrParts.append('%04d' % date.getYear())
		else:
			dateStrParts.append(self.__UNKNOWN)
		if date.hasMonth():
			dateStrParts.append(
				self.__MONTH_NAMES[date.getMonth()-1]
			)
		else:
			dateStrParts.append(self.__UNKNOWN)
		if date.hasDay():
			dateStrParts.append(str(date.getDay()))
		else:
			dateStrParts.append(self.__UNKNOWN)

		return ' '.join(dateStrParts)


	def __updateLabel(self, date=None, error=False):
		"""
		Update the info label as the formatted form of the given Date,
		or the Date this editor is for if none is given.
		"""
		if error:
			self.__label.setText('parse error')
			self.__label.setEnabled(True)
		else:
			self.__label.setText(self.__format(date or self.__date))
			self.__label.setEnabled(date is not None)


	def __updateField(self):
		"""
		Update the editing field to match the Date being edited.
		(Does nothing if the field's current text, when parsed,
		matches the current state of the Date.)
		"""
		with Util.Undo.UndoCaptureDisableGuard():
			parsedDate = self.__parse(str(self.__field.text()))
		if parsedDate != self.__date:
			self.__field.setText(self.__format(self.__date))


	def __fieldEdited(self, qstr):
		"""Update the info label, but don't affect the Date yet."""
		with Util.Undo.UndoCaptureDisableGuard():
			parsedDate = self.__parse(str(qstr))
		if parsedDate:
			self.__updateLabel(date=parsedDate)
		else:
			self.__updateLabel(error=True)


	def __editingFinished(self):
		"""
		If the current edit field text can be parsed, set the Date,
		otherwise revert the edit field's text to match the Date.
		"""
		with Util.Undo.UndoCaptureDisableGuard():
			d = self.__parse(str(self.__field.text()))
		if d and (d != self.__date):
			with Util.Undo.UndoGroupGuard() as g:
				self.__updateForChanges = False
				parts = []
				try:
					parts = _Assign(self.__date, d)
				finally:
					self.__updateForChanges = True
				partsStr = Util.Language.List(parts)
				g.setName('set %s %s' %
					(self.__date.getName(), partsStr))
		self.__updateField()
		self.__updateLabel()


	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Escape:
			event.accept()
			self.__updateField()
			self.__updateLabel()
		else:
			return QtGui.QWidget.keyPressEvent(self, event)



def _Assign(destDate, srcDate):
	"""
	Set values on destDate from srcDate, and return a list of string
	descriptors of the parts which were set.
	"""
	affected = []
	for part in ('year', 'month', 'day'):
		aName = part.capitalize()

		if getattr(srcDate, 'has'+aName)():
			v = getattr(srcDate, 'get'+aName)()
			if not getattr(destDate, 'has'+aName)() or \
			getattr(destDate, 'get'+aName)() != v:
				getattr(destDate, 'set'+aName)(v)
			affected.append(part)
		elif getattr(destDate, 'has'+aName)():
			getattr(destDate, 'clear'+aName)()
			affected.append(part)

	return affected


