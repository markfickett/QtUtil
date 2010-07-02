"""
save UI settings
"""

__all__ = [
	'GroupGuard',
	'ArrayReadGuard',
	'ArrayWriteGuard',

	'WriteWidgetGeometry',
	'ReadWidgetGeometry',
]

from Manifest import QtGui, QtCore, logging

log = logging.getLogger('Settings')



class GroupGuard(object):
	def __init__(self, settings, groupName):
		self.__settings = settings
		self.__groupName = str(groupName)
	def __enter__(self):
		self.__settings.beginGroup(self.__groupName)
	def __exit__(self, excClass, excObj, tb):
		self.__settings.endGroup()

class _ArrayGuard(object):
	def __init__(self, settings, arrayName):
		self._settings = settings
		self._arrayName = arrayName

class ArrayReadGuard(_ArrayGuard):
	def __enter__(self):
		return self._settings.beginReadArray(self._arrayName)
	def __exit__(self, excClass, excObj, tb):
		self._settings.endArray()

class ArrayWriteGuard(_ArrayGuard):
	def __enter__(self):
		self._settings.beginWriteArray(self._arrayName)
	def __exit__(self, excClass, excObj, tb):
		self._settings.endArray()


WIDGET_POS_NAME = 'pos'
WIDGET_SIZE_NAME = 'size'


def WriteWidgetGeometry(settings, name, widget):
	with GroupGuard(settings, name):
		pos = widget.pos()
		settings.setValue(WIDGET_POS_NAME, QtCore.QVariant(pos))
		size = widget.size()
		settings.setValue(WIDGET_SIZE_NAME, QtCore.QVariant(size))


def ReadWidgetGeometry(settings, name, widget):
	with GroupGuard(settings, name):
		pos = settings.value(WIDGET_POS_NAME).toPoint()
		if not pos.isNull():
			widget.move(pos)
		size = settings.value(WIDGET_SIZE_NAME).toSize()
		if size.isValid() and not (size.isNull() or size.isEmpty()):
			widget.resize(size)



