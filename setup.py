from setuptools import setup
import pymod

with open('README.md', 'r', encoding='utf-8') as fd:
  setup(
      name='pymod',
      version=pymod.__version__,
      author='chengscott',
      maintainer='chengscott',
      description='Simple Environment Variable Manager',
      long_description=fd.read(),
      long_description_content_type='text/markdown',
      url='https://github.com/chengscott/pymod',
      license='BSD',
      packages=['pymod'],
      entry_points={
          'console_scripts': ['pymod = pymod:run_main'],
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Topic :: System :: Shells',
      ],
  )
