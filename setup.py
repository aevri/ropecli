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


# -----------------------------------------------------------------------------
# Copyright (C) 2019 Angelos Evripiotis.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------
