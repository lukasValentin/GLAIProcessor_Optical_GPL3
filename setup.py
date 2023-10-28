from setuptools import setup, find_packages

setup(
    name='glai_processor',
    version='0.1',
    description='A package to invert satellite data to retrieve the green leaf area index (GLAI) and other vegetation traits.',
    author='Lukas Valentin Graf',
    author_email='lukas.graf@terensis.io',
    packages=find_packages(),
    install_requires=[
        'rio-cogeo',
        'git+https://github.com/EOA-team/eodal',
        'git+https://github.com/EOA-team/rtm_inv',
    ],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
