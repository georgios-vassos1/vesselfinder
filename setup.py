from setuptools import setup, find_packages, Command
from os import path

import os


here = path.abspath(path.dirname(__file__))

# stackoverflow.com/a/3780822
class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

# with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#     long_description = f.read()

setup(
    name="vessel-tracker",
    version="0.0.0",
    description="A collection of python modules for scraping data from vesselfinder.com.",
    author="George Vassos",
    author_email="georgios.vassos1@maersk.com",
    classifiers=[
            'Development Status :: 3 - Alpha',
            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Build Tools',
            # Pick your license as you wish
            'License :: OSI Approved :: MIT License',
            # Specify the Python versions you support here. In particular, ensure
            # that you indicate you support Python 3. These classifiers are *not*
            # checked by 'pip install'. See instead 'python_requires' below.
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3 :: Only',
        ],
    packages=find_packages(where='vessel_tracker'),
    python_requires='>=3.9',
    install_requires=[
        'numpy==1.26.1',
        'pandas==2.1.1',
        'playwright==1.15.3',
        'httpx==0.19.0',
        'aiohttp==3.7.4',
        'requests==2.26.0',
        'urllib3==1.26.7',
        'beautifulsoup4==4.10.0',
    ],
    cmdclass={
        'clean': CleanCommand,
    },
    tests_require=['pytest'],
    license='MIT',
)
