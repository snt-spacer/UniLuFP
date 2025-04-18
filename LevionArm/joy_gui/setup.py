from setuptools import find_packages, setup

package_name = "joy_gui"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "PyQt6"],
    zip_safe=True,
    maintainer="akiyoshi",
    maintainer_email="uchida.akiyoshi.s3@dc.tohoku.ac.jp",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "joystick_pad = joy_gui.joystick_pad:main",
            "joint_velocity_publisher_gui = joy_gui.joint_velocity_publisher_gui:main",
        ],
    },
)
