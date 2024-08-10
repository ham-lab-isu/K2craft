from setuptools import setup, find_packages

setup(
    name="Kaw2FFFControl",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pypylon", "opencv-python", "matplotlib", "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "kaw2fffcontrol=main:main",
        ],
    },
)
