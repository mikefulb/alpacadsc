# setup.py for the Alpaca Setting Circles Driver

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

# get version
from alpacadsc import __version__ as AlpacaDSCDriver_Version

setup(

    name='alpacadsc',  # Required

    version=AlpacaDSCDriver_Version,  # Required

    description='Digital setting circles support with Alpaca REST API',  # Optional

    long_description=long_description,  # Optional

    long_description_content_type='text/markdown',  # Optional (see note above)

    url='https://github.com/msf/alpacadsc',  # Optional

    author='Michael Fulbright',  # Optional

    author_email='mike.fulbright@pobox.com',  # Optional

    license='GPLv3',

    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: End Users/Desktop',
        'Topic :: Scientific/Engineering :: Astronomy',

        'License :: OSI Approved :: GNU General Public License (GPL)',

        'Operating System :: OS Independent',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='Alpaca',  # Optional

    package_dir={},  # Optional

    packages=find_packages(include=['alpacadsc']),  # Required

    python_requires='>=3.7, <4',

    install_requires=['Flask>=1.1',
                      'flask-restx>=0.2.0',
                      'astropy>=1.10',
                      'pyserial>=3',
                      'pyyaml>=5.3'],  # Optional

    extras_require={}, # Optional

    setup_requires=['flake8', 'pytest-runner', 'astropy'],

    tests_require=['pytest', 'pytest-flask', 'pyfakefs', 'astropy'],

    package_data={}, #{'': 'docs/build/html/*'},# Optional

    include_package_data = True,

    data_files=[],  # Optional

    entry_points={  # Optional
        'console_scripts': [
            'alpacadsc = alpacadsc.startservice:main',
        ],
    },

    project_urls={  # Optional
#        'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
#        'Funding': 'https://donate.pypi.org',
#        'Say Thanks!': 'http://saythanks.io/to/example',
#        'Source': 'https://github.com/pypa/sampleproject/',
    },
)

