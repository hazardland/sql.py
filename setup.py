from setuptools import setup

setup(name='pgsql-table',
      description='light PosgreSQL ORM with JSON model config',
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      author='Vakhtang Zardiashvili',
      author_email='hazardland@gmail.com',
      license='MIT',
      version='0.4.7',
      keywords='orm, pgsql, postgresql, model',
      packages=["sql"],
      url='https://github.com/hazardland/sql.py',
      python_requires='>=3.6',
      install_requires=['python_dateutil']
     )
