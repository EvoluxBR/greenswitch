#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


with open('README.rst', 'rb') as f:
    readme = f.read().decode('utf-8')

with open('requirements.txt') as f:
    requires = f.readlines()

setup(
    name='greenswitch',
    version='0.0.16',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=requires
)
