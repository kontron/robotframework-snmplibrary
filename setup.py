#!/usr/bin/env python

from setuptools import setup
import sys
sys.path.insert(0, 'src')

def main():
    setup(name = 'robotframework-snmplibrary',
            version = '0.1',
            description = 'SNMP Library for Robot Framework',
            author_email = 'michael.walle@kontron.com',
            package_dir = { '' : 'src' },
            packages = [ 'HpiLibrary' ],
            install_requires = [ 'robotframework', 'pysnmp' ]
    )

if __name__ == '__main__':
    main()
