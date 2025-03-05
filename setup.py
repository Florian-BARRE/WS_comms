from setuptools import setup, find_packages

setup(
    name="wscomms",
    version="0.1.4",
    author="Florian BARRE",
    author_email="florian.barre78@gmail.com",
    description="A WebSocket module enabling real-time communication between a server and multiple clients through a symmetric API, ensuring a consistent and easy-to-use interface on both ends.",
    long_description=open("./ReadMe.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Florian-BARRE/WS_comms",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        "aiohappyeyeballs>=2.4.4",
        "aiohttp>=3.11.11",
        "aiosignal>=1.3.2",
        "attrs>=25.1.0",
        "colorama>=0.4.6",
        "contourpy>=1.3.1",
        "cycler>=0.12.1",
        "fonttools>=4.55.8",
        "frozenlist>=1.5.0",
        "idna>=3.10",
        "kiwisolver>=1.4.8",
        "loggerplusplus>=0.1.4",
        "matplotlib>=3.10.0",
        "multidict>=6.1.0",
        "numpy>=2.2.2",
        "packaging>=24.2",
        "pillow>=11.1.0",
        "propcache>=0.2.1",
        "pyparsing>=3.2.1",
        "python-dateutil>=2.9.0.post0",
        "six>=1.17.0",
        "yarl>=1.18.3",
    ],
    include_package_data=True,
)
