#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(name='gnucash-invoice',
    version='1.0.0',
    description='GnuCash Latex Invoice Generator',
    url='',
    author='ElectroOptical Innovations, LLC.',
    author_email='simon.hobbs@electrooptical.net',
    license='BSD',
    packages=find_packages(),
    install_requires=[
        'click',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    scripts=['bin/invoice-maker'],
    include_package_data=True,
    zip_safe=True
)
