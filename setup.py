import os

from setuptools import setup, find_packages

# from etc.get_git_version import get_version


def read(fname):
    readme_file_path = os.path.join(os.path.dirname(__file__), fname)

    if os.path.exists(readme_file_path) and os.path.isfile(readme_file_path):
        readme_file = open(readme_file_path)
        return readme_file.read()
    else:
        return "The SoftFIRE integration test"


packages = find_packages()

setup(
    name="softfire-integration-test",
    # version=get_version(),
    version='0.0.1',
    author="SoftFIRE",
    author_email="softfire@softfire.eu",
    description="The SoftFIRE integration test",
    license="Apache 2",
    keywords="python experiment manager softfire integration test",
    url="http://softfire.eu/",
    packages=packages,
    scripts=["softfire-integration-test"],
    install_requires=[
        'requests'
    ],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: Apache Software License"
    ]
)
