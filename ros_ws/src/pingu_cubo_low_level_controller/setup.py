from setuptools import find_packages, setup
import os 
from glob import glob

package_name = 'pingu_cubo_low_level_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*_launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ricard Marsal I Castan',
    maintainer_email='ricard.marsal@unilu',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'minimal_thruster_publisher_px4 = pingu_cubo_low_level_controller.minimal_thruster_publisher_px4:main',
        ],
    },
)
