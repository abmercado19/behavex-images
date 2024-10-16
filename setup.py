# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.install import install as _install


class Install(_install):
    """Class needed for install package"""

    def run(self):
        """run installation"""
        _install.run(self)


with open('README.md', 'r') as fh:
    long_description = fh.read()


setup(
    # Application name:
    name='behavex-images',
    # Version number (initial):
    version='3.0.7',
    license="MIT",
    # Application author details:
    author='Hernan Rey, Ana Mercado',
    author_email='hernanrey@gmail.com, abmercado19@gmail.com',
    url='https://github.com/abmercado19/behavex-images',
    platforms=['any'],
    # Packages
    packages=[
        'behavex_images',
        'behavex_images.utils',
        'behavex_images.utils.support_files',
    ],
    # Include additional files into the package
    include_package_data=True,
    description='BehaveX extension library to attach images to the test execution report.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'behave',
        'behavex',
        'numpy',
        'pillow',
    ],
    cmdclass={'install': Install},
)
