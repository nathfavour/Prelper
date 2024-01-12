from setuptools import setup, find_packages

setup(
    name='prelper',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'prelper = prelper.main:main',
        ],
    },
    install_requires=[
        # Add your dependencies here
    ],
    author='nathfavour',
    description='A helpful command line tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/nathfavour/prelper',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)