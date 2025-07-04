from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "simulation_core",              # Name of the module you'll import in Python
        ["simulation_core.pyx"],        # Path to your Cython source file
        # Optional: uncomment if you need specific C/C++ compiler arguments
        # extra_compile_args=["-O3", "-march=native"], # Example for GCC/Clang for maximum optimization
    )
]

setup(
    name='Sandbox Simulation', # A descriptive name for your project
    ext_modules=cythonize(
        extensions,
        compiler_directives={'language_level': "3"}, # Ensures Python 3 syntax compatibility
        annotate=True # Generates an HTML report showing Python vs. C code, very useful for optimization
    )
)