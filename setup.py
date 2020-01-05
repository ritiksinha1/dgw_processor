from setuptools import setup, find_packages

with open('README.md', 'r') as readme:
  long_description = readme.read()

setup(
    author='Christopher Vickery',
    author_email='christopher.vickery@qc.cuny.edu',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    description='Process Degreeworks Scribe Blocks',
    include_package_data=True,
    keywords='dgw_processor',
    long_description=long_description,
    long_description_content_type='text/markdown',
    name='dgw_processor',
    packages=find_packages(include=['dgw_processor', 'dgw_processor.*']),
    python_requires='>= 3.6',
    url='https://github.com/cvickery/dgw_processor',
    version='0.1.0',
    zip_safe=False,
)
