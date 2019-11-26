import fastentrypoints
import setuptools

setuptools.setup(
    name='rope-cli',
    author='Angelos Evripiotis',
    author_email='angelos.evripiotis@gmail.com',
    zip_safe=False,
    packages=[
        'ropecli',
    ],
    entry_points={
        'console_scripts': [
            'rope=ropecli:main',
        ]
    },
    install_requires=[
        'click',
        'rope',
    ],
    extras_require={
        'dev': [
            'pytest',
        ]
    },
    python_requires='>=3.6',
)
