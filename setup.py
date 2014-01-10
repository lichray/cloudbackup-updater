import os
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='cloudbackup-updater',
    version='0.1',
    description='Auto-updater for the Rackspace Cloud Backup agent',
    author='Zhihao Yuan',
    author_email='zhihao.yuan@rackspace.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cloudbackup-updater = cloudbackup_updater:main',
        ],
    },
    zip_safe=True,
    license='BSD',
    keywords=['rackspace', 'cloudbackup', 'daemon'],
    url='https://github.com/lichray/cloudbackup-updater',
    long_description=read('README.rst'),
    install_requires=open('tools/requires', 'rt').readlines(),
    tests_require=open('tools/test-requires', 'rt').readlines(),
)
