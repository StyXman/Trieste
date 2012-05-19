#!/usr/bin/python

from distutils.core import setup, Extension

setup(name='Trieste',
      version='0.1b-1',
      description="Trieste is a Distributed File System.",
      long_description="""
Trieste is a DFS with allocation policy support and low configuration.""",
      author='Marcos D. Dione',
      author_email='mdione@grulic.org.ar',
      url='http://plantalta.homelinux.net/~mdione/projects/Trieste',
      license='GPL',
      packages=['Trieste',
                'Trieste.common',
                'Trieste.umbie',
                'Trieste.vice',
                'Trieste.virtue',
                'fuse',
                'fuse.python',
                ],
      # ext_modules= [Extension('fuse.phyton._fuse', ['_fusemodule.c'])],
      classifiers= ['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: Spanish',
                   'Natural Language :: English',
                   'Operating System :: POSIX',
                   'Programming Language :: Python',
                   'Topic :: Internet',
                   ],
      )
