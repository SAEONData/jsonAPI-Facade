from setuptools import setup

version = '0.1'

setup(
    name='jsonAPI-Facade',
    version=version,
    description='A web service providing json* interfaces to the CKAN back-end',
    url='https://github.com/SAEONData/jsonAPI-Facade',
    author='Mark Jacobson',
    author_email='mark@saeon.ac.za',
    license='MIT',
    packages=[],
    install_requires=[
        'cherrypy',
        'routes',
        'requests',
    ],
    python_requires='>=3',
    data_files=[('static', ['static/index.html', 'static/sample_metadata.json'])],
)
