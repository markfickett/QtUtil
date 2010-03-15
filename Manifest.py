"""
Import modules used only in the UI.
"""

from PyQt4 import QtCore, QtGui

import code, traceback
import enum

from FamilyTree import logging, sys, rlcompleter, os

if not hasattr(sys, 'ps1'):
        sys.ps1 = '>>> '
if not hasattr(sys, 'ps2'):
        sys.ps2 = '... '

