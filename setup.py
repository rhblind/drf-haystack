# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name="drf-haystack",
    version="1.4",
    description="Makes Haystack play nice with Django REST Framework",
    long_description="Implements a ViewSet, some filters and serializers in order to play nice with Haystack.",
    author="Rolf Håvard Blindheim, Eirik Krogstad",
    author_email="rolf.blindheim@inonit.no, eirik.krogstad@inonit.no",
    url="https://github.com/inonit/drf-haystack",
    download_url="https://github.com/inonit/drf-haystack.git",
    license="MIT License",
    packages=[
        "drf_haystack",
    ],
    include_package_data=True,
    install_requires=[
        "Django>=1.5.0",
        "djangorestframework>=2.4.4",
        "django-haystack>=2.3.1"
    ],
    tests_require=[
        "nose",
        "mock",
        "coverage",
        "unittest2",
        "elasticsearch>=1.4.0",
    ],
    zip_safe=False,
    test_suite="tests.runtests.start",
    classifiers=[
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
