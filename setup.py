from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="vessel_tracking",
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
    packages=find_packages(where='sourcing'),
    python_requires='>=3.9',
    tests_require=['pytest'],
)


