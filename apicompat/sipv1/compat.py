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

def pystring(qvar):
    return unicode(qvar.toString()) if hasattr(qvar, 'toString') else unicode(qvar)

__builtin__.pystring = pystring
def pylist(qvar):
    return list(qvar.toList()) if hasattr(qvar, 'toList') else qvar
__builtin__.pylist = pylist
def pyint(qvar):
    if hasattr(qvar, 'toInt'): 
        val, ok = qvar.toInt()
        if not ok:
            raise ValueError('QVariant conversion error')
        return int(val)
    else:
        return qvar
__builtin__.pyint = pyint
def pyfloat(qvar):
    if hasattr(qvar, 'toFloat'): 
        val, ok = qvar.toFloat()
        if not ok:
            raise ValueError('QVariant conversion error')
        return float(val)
    else:
        return qvar
__builtin__.pyfloat = pyfloat
def pystringlist(qvar):
    return list(map(lambda s: unicode(s), qvar.toStringList())) if hasattr(qvar, 'toStringList') else qvar
__builtin__.pystringlist = pystringlist
def pybytearray(qvar):
    return bytearray(qvar.toByteArray()) if hasattr(qvar, 'toByteArray') else qvar
__builtin__.pybytearray = pybytearray
def pyobject(qvar):
    return qvar.toPyObject() if hasattr(qvar, 'toPyObject') else qvar
__builtin__.pyobject = pyobject
