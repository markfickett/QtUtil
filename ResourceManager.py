"""
Manage retrieval of support files for the UI.
"""

__all__ = [
	'AppendResourcePath',
	'GetFile',
	'GetIcon',
]

from Manifest import QtCore, QtGui, os, logging
log = logging.getLogger('ResourceManager')

ICON_SUBDIR = 'icons'

global resourcePaths
resourcePaths = []
"""list of directories in which to search for resource files"""

global imageCache
imageCache = {}
"""absolute path -> (QPixmap, QIcon)"""


def AppendResourcePath(newPath):
	path = os.path.abspath(newPath)
	if os.path.isdir(path):
		global resourcePaths
		if path not in resourcePaths:
			resourcePaths.append(path)
			log.debug("adding resource path '%s'" % path)
	else:
		log.warning(
			"ignoring resource path '%s': not a directory" % path)


def GetFile(localFilename):
	"""
	Return an absolute path for the given (probably) local filename,
	or None of no existing file can be found.
	"""
	if os.path.isabs(localFilename):
		absFilename = localFilename
		if os.path.isfile(absFilename):
			return absFilename
		else:
			return None
	else:
		global resourcePaths
		for resourceDir in resourcePaths:
			absFilename = os.path.join(resourceDir, localFilename)
			if os.path.isfile(absFilename):
				return absFilename
		return None


def _GetImage(path):
	global imageCache
	imageData = imageCache.get(path)
	if not imageData:
		if path:
			pixmap = QtGui.QPixmap(path)
		else:
			pixmap = QtGui.QPixmap()
		icon = QtGui.QIcon(pixmap)
		imageData = (pixmap, icon)
		imageCache[path] = imageData

		if pixmap.isNull():
			log.warning("null QPixmap from '%s'" % path)
	return imageData


def GetIcon(filename):
	path = GetFile(os.path.join(ICON_SUBDIR, filename))
	pixmap, icon = _GetImage(path)
	return icon


