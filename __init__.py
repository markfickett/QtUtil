
import Settings
import Drawing
import ResourceManager

from InteractivePythonWidget import *

from Manifest import os
localDir = os.path.dirname(__file__)
resourceDir = os.path.normpath(os.path.join(localDir, 'resources'))
ResourceManager.AppendResourcePath(resourceDir)
del localDir, resourceDir

