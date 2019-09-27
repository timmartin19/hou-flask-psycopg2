#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

requirements = ["psycopg2", "python-rapidjson", "flask", "werkzeug"]

setup(
    name="hou-flask-psycopg2",
    version="0.0.3",
    description="Highly Opinionated Utils: Flask Psycopg2",
    long_description=readme + "\n\n" + history,
    author="Tim Martin",
    author_email="oss@timmartin.me",
    url="https://github.com/timmartin19/hou-flask-psycopg2",
    packages=["hou_flask_psycopg2"],
    package_dir={"hou_flask_psycopg2": "hou_flask_psycopg2"},
    package_data={
        "hou-flask-psycopg2": ["README.md", "HISTORY.md"]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords="oss_auth",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    test_suite="tests",
)
