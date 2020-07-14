# py_skel

I decided I should stop recreating the wheel every time I want to jump in to a new Python project, so I made this.

It's not fancy or complicated - couple of useful module files I use a lot, a template file so I don't have to stare at a blank screen to get started throwing code at the wall, that's about it. Hey, it should have a template README.md too, shouldn't it...

## Installation

Checkout the latest version of this repo, then copy the non-.git files to a new repo folder and set up a virtual environment. 

```bash
git clone https://github.com/mbeland/py_skel.git
python3 -m venv new_project
cp -r py_skel/.gitignore py_skel/*
```

## Usage

The template provides a simple PEP8-compliant shell for creating new code, including a basic framework for command line arguments and standardized format usage help. The multitool folder contains simple modules I reuse constantly, and a init file so the functions are available directly through the multitool package name. As I clean up and standardize more of my toolkit they go in there; I won't let myself use them until they're there, which hopefully will put pressure on me to make that happen. Currently those files are 

  * [multitool/fileparse.py](https://github.com/mbeland/py_skel/blob/release/multitool/fileparse.py) - Simple module for parsing data files - essentially an abstraction layer of the full csv module for my own common preferences (Modified from David Beazley's excellent [Practical Python](https://dabeaz-course.github.io/practical-python/) course)

  * [multitool/tableformat.py](https://github.com/mbeland/py_skel/blob/release/multitool/tableformat.py) - Simple formatting module for outputting table data in a variety of formats (Modified from David Beazley's excellent [Practical Python](https://dabeaz-course.github.io/practical-python/) course)

  * [multitool/timethis.py](https://github.com/mbeland/py_skel/blob/release/multitool/timethis.py) - Another valuable item snagged from David Beazley's excellent [Practical Python](https://dabeaz-course.github.io/practical-python/) course, a simple wrapper function useful for seeing how long functions take to execute

  * [multitool/log.py](https://github.com/mbeland/py_skel/blob/release/multitool/log.py) - a class definition for the standard logging module, making one-line consistent creation of error logs straighforward.
  
  * [multitool/sshclient.py](https://github.com/mbeland/py_skel/blob/release/multitool/sshclient.py) - a Paramiko wrapper to standardize the use of SSH for programmatic functions. Requires installation of Paramiko and all optional packages; recommend using ```python -m pip install paramiko[all]```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
