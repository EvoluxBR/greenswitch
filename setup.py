#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('requirements.txt') as f:
    requires = f.readlines()

setup(
    name='greenswitch',
    version='0.0.8',
    description=u'Battle proven FreeSWITCH Event Socket Protocol client implementation with Gevent.',
    long_description=readme,
    author=u'Ítalo Rossi',
    author_email=u'italorossib@gmail.com',
    url=u'https://github.com/evoluxbr/greenswitch',
    license=u'MIT',
    packages=find_packages(exclude=('tests', 'docs')),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=requires
)
