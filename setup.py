from distutils.core import setup

setup(
    name='houseofreps',
    version='0.1dev',
    packages=['houseofreps',],
    package_data={'houseofreps': ['apportionment.csv']},
    license='MIT',
    long_description=open('README.md').read(),
)
