MetaData = {
       'name':'CocoPy',
       'version':'1.1.0rc',
       'description':'Python implementation of the famous CoCo/R LL(k) compiler generator.',
       'url':'http://www.ssw.uni-linz.ac.at/coco',
       'author':'Ron Longo',
       'author_email':'ron.longo@cox.net',
       'license':'GPL',
       'packages':[ '' ],
       'data_files':[ ( 'documentation', [ 'documentation/*' ] ),
                      ( 'examples',      [ 'examples/*'      ] ),
                      ( 'frames',        [ 'frames/*'        ] ),
                      ( 'pimaker',       [ 'pimaker/*'       ] ),
                      ( 'sources',       [ 'sources/*'       ] ),
                      ( 'testSuite',     [ 'testSuite/*'     ] ) ],
       'classifiers':[
                      'Development Status :: 4 - Beta',
                      'Environment :: Console',
                      'Intended Audience :: Developers',
                      'Intended Audience :: Education',
                      'Intended Audience :: Information Technology',
                      'Intended Audience :: Science/Research',
                      'License :: OSI Approved :: GNU General Public License (GPL)',
                      'Natural Language :: English',
                      'Programming Language :: Python',
                      'Topic :: Scientific/Engineering',
                      'Topic :: Scientific/Engineering :: Human Machine Interfaces',
                      'Topic :: Scientific/Engineering :: Information Analysis',
                      'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
                      'Topic :: Software Development :: Code Generators',
                      'Topic :: Software Development :: Compilers',
                      'Topic :: Software Development :: Interpreters',
                      'Topic :: Software Development :: Pre-processors',
                      'Topic :: System :: Shells',
                      'Topic :: Text Processing :: General',
                      'Topic :: Text Processing :: Linguistic'
                   ]
     }

VersionInfo = {
   '1.1.0rc': {
      'changes':  [ "Coco/R now passes all tests of the official Coco/R test suite" ],
      'bugfixes': [ ],
      'contirubtions': [ ]
      },

   '1.0.10b2':{
      'changes':  [ "Updated builder and renamed it to pimaker" ],
      'bugfixes': [ "Many code generator bug fixes" ],
      'contributions': [ "Wayne Wiitanen has contributed a version of the EXPR example that works with CocoPy." ]
      },

   '1.0.9b2': {
      'changes':  [ "Simplified the Errors class and error handling.",
                    "Completed a first version of my builder application." ],
      'bugfixes': [ "Repaired a bug in SemErr() didn't work properly." ]
      },

   '1.0.7b1': {
      'changes':  [ ],
      'bugfixes': [ "Repaired LINUX bug found in v1.0.6b1" ]
      },

   '1.0.6b1': {
      'changes':  [ "Completed a beta version of builder.py",
                    "Updated README.txt to describe builder.py",
                    "Removed HowToBootstrap.txt from Documents" ],
      'bugfixes': [ "Coco.atg does not bootstrap on LINUX." ]
      }
   }
