from setuptools import setup

version = '0.3'

setup(
    name='jsonAPI-Facade',
    version=version,
    description='A web service providing json* interfaces to the CKAN back-end',
    url='https://github.com/SAEONData/jsonAPI-Facade',
    author='Mark Jacobson',
    author_email='mark@saeon.ac.za',
    license='MIT',
    packages=['jsonapi'],
    install_requires=[
        'cherrypy',
        'routes',
        'ckanapi',
    ],
    python_requires='~=3.5',
)
