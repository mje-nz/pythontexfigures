from setuptools import setup

setup(name='pythontexfigures',
      version='0.1pre',
      description='PythonTeX figure generation library',
      url='https://github.com/mje-nz/pythontexfigures',
      author='Matthew Edwards',
      author_email='mje-nz@users.noreply.github.com',
      license='BSD 3-Clause',
      packages=['pythontexfigures'],
      python_requires='>=3.5',
      install_requires=[
            'matplotlib',
            'pygments'  # for pythontex
      ],
      zip_safe=False)
