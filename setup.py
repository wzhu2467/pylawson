from setuptools import setup

setup(
    name='pylawson',
    version='0.2',
    description='Infor Lawson IOS API Wrapper',
    long_description=open('README.md').read(),
    keywords='infor lawson erp',
    url='https://github.com/indepndnt/pylawson',
    author='Joe Carey',
    author_email='joe@accountingdatasolutions.com',
    license='Apache 2.0',
    packages=['pylawson', 'pylawson.client'],
    install_requires=['beautifulsoup4', 'requests'],
    extras_require={
        'sec_api': ['clr']
    },
    zip_safe=False
)
