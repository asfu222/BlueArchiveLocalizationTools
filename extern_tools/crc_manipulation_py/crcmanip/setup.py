from setuptools import setup, Extension

module = Extension('crcmanip.fastcrc', sources=['fastcrc.c'])

setup(name='crcmanip',
      version='1.0',
      description='CRC manipulation library',
      ext_modules=[module])
