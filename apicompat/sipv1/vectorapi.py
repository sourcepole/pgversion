# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ApiCompat
                                 A QGIS plugin
 API compatibility layer
                              -------------------
        begin                : 2013-07-02
        copyright            : (C) 2013 by Pirmin Kalberer, Sourcepole
        email                : pka@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from qgis.core import *


from decorators import *

def vectorapiv1():
  return not hasattr(QgsVectorLayer, 'getFeatures')

@add_method(QgsVectorLayer)
def getFeatures(self):
    self.select([])
    return self
