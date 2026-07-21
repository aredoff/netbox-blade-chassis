from setuptools import find_packages, setup

setup(
    name='netbox_blade_chassis',
    version='0.1.0',
    description='NetBox plugin for blade chassis visualization in rack elevations.',
    long_description='Visualize blade server bays inside parent devices in rack SVG elevations.',
    author='NetBox Blade Chassis',
    license='Apache-2.0',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.10',
)
