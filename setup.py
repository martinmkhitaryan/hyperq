import os

from Cython.Build import cythonize
from setuptools import Extension, setup

cxxflags = os.environ.get('CXXFLAGS', '-std=c++20 -O3 -Wall -Wextra')
compile_args = cxxflags.split()

extensions = [
    Extension(
        "hyperq.hyperq",
        sources=["src/hyperq/hyperq.pyx"],
        language="c++",
        extra_compile_args=compile_args,
        extra_link_args=["-std=c++20"],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'nonecheck': False,
            'cdivision': True,
            'infer_types': True,
            'profile': False,
            'linetrace': False,
            'embedsignature': False,
            'always_allow_keywords': False,
            'optimize.use_switch': True,
        },
    )
)
