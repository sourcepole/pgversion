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
import __builtin__

#Define backwards compatibility functions
def pystring(qvar):
    return unicode(qvar)
__builtin__.pystring = pystring
def pylist(qvar):
    return list(qvar)
__builtin__.pylist = pylist
def pyint(qvar):
    return int(qvar)
__builtin__.pyint = pyint
def pyfloat(qvar):
    return float(qvar)
__builtin__.pyfloat = pyfloat
def pystringlist(qvar):
    return list(qvar)
__builtin__.pystringlist = pystringlist
def pybytearray(qvar):
    return bytearray(qvar)
__builtin__.pybytearray = pybytearray
def pyobject(qvar):
    return qvar
__builtin__.pyobject = pyobject
