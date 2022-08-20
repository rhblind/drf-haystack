# -*- coding: utf-8 -*-

import re
import os

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

setup(
    name="drf-haystack",
    version=get_version("drf_haystack"),
    description="Makes Haystack play nice with Django REST Framework",
    long_description="Implements a ViewSet, FiltersBackends and Serializers in order to play nice with Haystack.",
    author="Rolf Håvard Blindheim",
    author_email="rhblind@gmail.com",
    url="https://github.com/rhblind/drf-haystack",
    download_url="https://github.com/rhblind/drf-haystack.git",
    license="MIT License",
    packages=[
        "drf_haystack",
    ],
    include_package_data=True,
    install_requires=[
        "Django>=2.2,<3.3",
        "djangorestframework>=3.7,<3.13",
        "django-haystack>=2.8,<=3.2",
        "python-dateutil"
    ],
    tests_require=[
        "nose",
        "coverage"
    ],
    zip_safe=False,
    test_suite="tests.run_tests.start",
    classifiers=[
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7"
)
