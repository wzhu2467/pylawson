from setuptools import setup

setup(name='pylawson',
      version='0.1',
      description='Infor Lawson IOS API Wrapper with ADFS Authentication',
      url='https://github.com/indepndnt/pylawson',
      author='Joe Carey',
      author_email='joecarey001@gmail.com',
      license='Apache 2.0',
      packages=['pylawson', 'pylawson.sec_api'],
      install_requires=['beautifulsoup4', 'requests'],
      zip_safe=False)
