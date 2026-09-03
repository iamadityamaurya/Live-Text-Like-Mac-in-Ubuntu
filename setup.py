from setuptools import setup, find_packages

setup(
    name="live-text-ocr",
    version="1.0.0",
    description="macOS Live Text–style OCR utility for Ubuntu",
    author="Aditya",
    packages=find_packages(),
    install_requires=[
        "pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "live-text-ocr = live_text_ocr.cli:main",
        ],
    },
    python_requires=">=3.8",
)
