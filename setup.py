from setuptools import setup

setup(name='pgsql-table',
      description='JSON definition based light ORM for PosgreSQL',
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      author='Vakhtang Zardiashvili',
      author_email='hazardland@gmail.com',
      license='MIT',
      version='0.3.3',
      keywords='orm, pgsql, postgresql, model',
      packages=["sql"],
      url='https://github.com/hazardland/sql.py',
      python_requires='>=3.6',
      install_requires=['python_dateutil']
     )
