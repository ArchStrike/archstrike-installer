#!/usr/bin/env python
import sys
import pathlib
from setuptools import setup

sys.path.append(pathlib.Path(__file__).resolve().parent)
import asinstaller  # noqa

setup(name="asinstaller",
      version=asinstaller.__version__,
      description="ArchStrike Installer",
      author="James Stronz",
      author_email="comrumino@archstrike.org",
      maintainer="James Stronz",
      maintainer_email="comrumino@archstrike.org",
      license="MIT",
      url="http://github.com/ArchStrike/archstrike-installer",
      packages=['asinstaller'],
      scripts=['bin/archstrike-installer', 'bin/archstrike-arbitration'],
      install_requires=["pyalpm"],
      platforms=["ArchLinux", "ArchLinux-based"],
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3.8",
          "Topic :: System :: Systems Administration",
      ],
      )
