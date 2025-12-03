from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tensorboard-flight",
    version="0.1.0",
    author="Lucas Wright",
    author_email="lhwright13@gmail.com",
    description="TensorBoard plugin for 3D flight trajectory visualization and analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lhwright13/tensorboard-flight-plugin",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "tensorboard>=2.11.0",
        "protobuf>=3.19.0",
        "numpy>=1.21.0",
        "werkzeug>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "tensorboard_plugins": [
            "flight = tensorboard_flight.plugin:FlightPlugin",
        ],
    },
    package_data={
        "tensorboard_flight": ["static/*"],
    },
    include_package_data=True,
    zip_safe=False,
)
