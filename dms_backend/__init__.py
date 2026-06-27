import sys
from copy import copy

# Monkeypatch django.template.context.BaseContext.__copy__ to fix Python 3.14 compatibility
try:
    from django.template.context import BaseContext
    
    def _safe_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _safe_copy
except ImportError:
    pass
