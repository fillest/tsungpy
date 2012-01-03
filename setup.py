import os
import sys
from setuptools import setup, find_packages


requires = [
	'lxml',
	'decorator',
]

setup(name='tsungpy',
      version='0.1',
      author_email='fsfeel@gmail.com',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = requires,
      )

