
import Settings
import Drawing
import ResourceManager

from InteractivePythonWidget import *

import os
localDir = os.path.dirname(__file__)
resourceDir = os.path.normpath(os.path.join(localDir, '..', '..', 'resources'))
ResourceManager.AppendResourcePath(resourceDir)

