from setuptools import setup

setup(
    name='pylawson',
    version='0.3',
    description='Infor Lawson IOS API Wrapper',
    long_description=open('README.rst').read(),
    keywords='infor lawson erp',
    url='https://github.com/indepndnt/pylawson',
    author='Joe Carey',
    author_email='joe@accountingdatasolutions.com',
    license='Apache 2.0',
    packages=['pylawson', 'pylawson.client'],
    install_requires=['beautifulsoup4', 'requests'],
    extras_require={
        'sec_api': ['pythonnet']
    },
    zip_safe=False
)
