"""
Provide utilities related to GUI drawing, supplemental to QStyle and QPalette.
"""

__all__ = [
	'GetErrorColor',
]

from Manifest import QtCore, QtGui


def GetErrorColor(customPalette=None):
	"""
	Get the color to use for foreground error elements,
	such as error text.
	"""
	palette = customPalette or QtGui.QApplication.palette()
	disabledTextColor = palette.color(QtGui.QPalette.Disabled,
		QtGui.QPalette.Text)
	h, s, v, a = disabledTextColor.getHsvF()
	return QtGui.QColor.fromHsvF(0, s + 0.6, v + 0.2)


