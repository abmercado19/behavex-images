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
    version='3.2.2',
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
        'pillow',
        'filelock; python_version>="3.8"',
    ],
    cmdclass={'install': Install},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Testing',
    ],
)
