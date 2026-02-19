from setuptools import find_packages, setup

package_name = 'px4_simple'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='akiyoshi',
    maintainer_email='uchida.akiyoshi.s3@dc.tohoku.ac.jp',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'px4_simple_node = px4_simple.px4_simple_node:main',
            'test_px4 = px4_simple.test_px4:main',
            'test_solenoid_valve_connection = px4_simple.test_solenoid_valve_connection:main',
            'low_level_thruster_control = px4_simple.low_level_thruster_control:main',
            'twist_thruster_actuator = px4_simple.twist_thruster_actuator:main',
            'thruster_test = px4_simple.thruster_test:main',
        ],
    },
)
