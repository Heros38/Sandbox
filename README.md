This project requires multiples lybraries that are not installed by default : pygame, pygame_widgets, numpy, numba.
You can import them using pip (for example 'pip install pygame')
To download the project you can do it either with git (git clone -b main https://github.com/Heros38/Sandbox.git) or by downloading the zip file.

To run the sandbox, just run the main.py file, you can mess around with settings in the config.py file.

Controls :
  * LMB to place element
  * RMB to replace by air

About the experimental version, it's not stable yet but provide significant performance boost :) you'll need to install cython, use python 3.12.2 (IMPORTANT) and use a C compiler to compile the pyx file if the compiled version isn't there.

I might add a more detailed explanation later.
