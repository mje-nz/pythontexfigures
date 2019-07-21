from setuptools import setup

with open("Readme.md") as f:
  long_description = f.read()

setup(name='pythontexfigures',
      version='0.1pre',
      description='Embed matplotlib figures into LaTeX documents using PythonTeX',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/mje-nz/pythontexfigures',
      author='Matthew Edwards',
      license='BSD 3-Clause',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: BSD License',
            'Operating System :: MacOS :: MacOS X',
            #'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            #'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Text Processing :: Markup :: LaTeX'

      ],
      packages=['pythontexfigures'],
      python_requires='>=3.5',
      install_requires=[
            'matplotlib',
            'pygments'  # for pythontex
      ],
      zip_safe=False)
