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

#http://blog.ianbicking.org/2007/08/08/opening-python-classes/

import types
import inspect

def add_method(obj):
    """
    Adds a function/method to an object.  Uses the name of the first
    argument as a hint about whether it is a method (``self``), class
    method (``cls`` or ``klass``), or static method (anything else).
    Works on both instances and classes.

        >>> class color:
        ...     def __init__(self, r, g, b):
        ...         self.r, self.g, self.b = r, g, b
        >>> c = color(0, 1, 0)
        >>> c      # doctest: +ELLIPSIS
        <__main__.color instance at ...>
        >>> @add_method(color)
        ... def __repr__(self):
        ...     return '<color %s %s %s>' % (self.r, self.g, self.b)
        >>> c
        <color 0 1 0>
        >>> @add_method(color)
        ... def red(cls):
        ...     return cls(1, 0, 0)
        >>> color.red()
        <color 1 0 0>
        >>> c.red()
        <color 1 0 0>
        >>> @add_method(color)
        ... def name():
        ...     return 'color'
        >>> color.name()
        'color'
        >>> @add_method(c)
        ... def name(self):
        ...     return 'red'
        >>> c.name()
        'red'
        >>> @add_method(c)
        ... def name(cls):
        ...     return cls.__name__
        >>> c.name()
        'color'
        >>> @add_method(c)
        ... def pr(obj):
        ...     print obj
        >>> c.pr(1)
        1
    """
    def decorator(func):
        is_class = (isinstance(obj, type)
                    or isinstance(obj, types.ClassType))
        args, varargs, varkw, defaults = inspect.getargspec(func)
        if not args or args[0] not in ('self', 'cls', 'klass'):
            # Static function/method
            if is_class:
                replacement = staticmethod(func)
            else:
                replacement = func
        elif args[0] == 'self':
            if is_class:
                replacement = func
            else:
                def replacement(*args, **kw):
                    return func(obj, *args, **kw)
                try:
                    replacement.func_name = func.func_name
                except:
                    pass
        else:
            if is_class:
                replacement = classmethod(func)
            else:
                def replacement(*args, **kw):
                    return func(obj.__class__, *args, **kw)
                try:
                    replacement.func_name = func.func_name
                except:
                    pass
        setattr(obj, func.func_name, replacement)
        return replacement
    return decorator


#http://moonbase.rydia.net/mental/blog/programming/a-monkeypatching-decorator-for-python.html
from functools import wraps

def patches(target, name, external_decorator=None):
  def decorator(patch_function):
    original_function = getattr(target, name)

    @wraps(patch_function)
    def wrapper(*args, **kw):
      return patch_function(original_function, *args, **kw)

    if external_decorator is not None:
      wrapper = external_decorator(wrapper)

    setattr(target, name, wrapper)
    return wrapper

  return decorator
