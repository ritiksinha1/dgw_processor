import setuptools

with open('README.md', 'r') as readme:
  long_description = readme.read()

setuptools.setup(name='dgw_processor',
                 version='0.0.3',
                 author='Christopher Vickery',
                 author_email='christopher.vickery@qc.cuny.edu',
                 description='Process Degreeworks Scribe Blocks',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://github.com/cvickery/dgw_processor',
                 packages=setuptools.find_packages(),
                 classifiers=['Programming Language :: Python :: 3',
                              'License :: OSI Approved :: MIT License',
                              'Operating System :: OS Independent',
                              ],
                 python_requires='>= 3.6',
                 )
