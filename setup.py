import os
from setuptools import setup


setup(
    name='cloudbackup-updater',
    version='0.1',
    description='Auto-updater for the Rackspace Cloud Backup agent',
    author='Zhihao Yuan',
    author_email='zhihao.yuan@rackspace.com',
    packages=['dotlock', 'pkgup'],
    scripts=['scripts/cloudbackup-updater.py'],
    zip_safe=True,
    license='BSD',
    keywords=['rackspace', 'cloudbackup', 'daemon'],
    url='https://github.com/lichray/cloudbackup-updater',
    install_requires=open('tools/requires', 'rt').readlines(),
    tests_require=open('tools/test-requires', 'rt').readlines(),
)
