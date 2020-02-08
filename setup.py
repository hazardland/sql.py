from setuptools import setup

setup(name='pgsql-table',
      description='Generate SQL clauses based on table JSON definitions, Create objects of your class from selected rows',
      long_description=open("README.md").read(),
      author='Vakhtang Zardiashvili',
      author_email='hazardland@gmail.com',
      license='BSD',
      version='0.1.0',
      keywords='orm, pgsql',
      packages=["sql"],
      url='https://github.com/hazardland/sql.py'
     )
