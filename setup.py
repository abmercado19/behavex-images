# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.install import install as _install


class Install(_install):
    """Class needed for install package"""

    def run(self):
        """run installation"""
        _install.run(self)


# Minimal setup.py for backward compatibility
# All configuration is now in pyproject.toml
setup(
    cmdclass={'install': Install},
)
