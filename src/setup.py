import setuptools
from setuptools import find_packages

setuptools.setup(
    name="rgbd_recorder",
    version="0.0.1",
    author="Mathieu De Coster",
    author_email="mathieu.decoster@ugent.be",
    description="Record RGB and depth streams with airo-mono",
    install_requires=[
        "numpy<=2.0",
        "opencv-contrib-python==4.8.1.78",
        "opencv-python-headless==4.8.1.78",
        "airo-typing @ git+https://github.com/airo-ugent/airo-mono@e20960e69c04033247ea5098f4c9c0ca577ab659#subdirectory=airo-typing",
        "airo-spatial-algebra @ git+https://github.com/airo-ugent/airo-mono@e20960e69c04033247ea5098f4c9c0ca577ab659#subdirectory=airo-spatial-algebra",
        "airo-camera-toolkit @ git+https://github.com/airo-ugent/airo-mono@e20960e69c04033247ea5098f4c9c0ca577ab659#subdirectory=airo-camera-toolkit",
        "airo-dataset-tools @ git+https://github.com/airo-ugent/airo-mono@e20960e69c04033247ea5098f4c9c0ca577ab659#subdirectory=airo-dataset-tools",
        "loguru==0.7.2",

    ],
    packages=find_packages(),
)
