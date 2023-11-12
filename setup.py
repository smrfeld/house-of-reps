import setuptools

# Load the long_description from README.md
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="houseofreps",
    version="0.1",
    author="smrfeld",
    author_email="oliver.k.ernst@gmail.com",
    description="Apportionment of representatives in U.S. House of Representatives.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smrfeld/house-of-reps/",
    packages=setuptools.find_packages(),
    package_data={'houseofreps': ['apportionment.csv']},
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "loguru",
        "mashumaro",
        "numpy",
        "pandas",
        "plotly",
        "pytest",
        "setuptools",
        "tqdm"
    ]
)