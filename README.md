# Naga

Naga is a remote systems management tool of sorts; it's slowly aggregated together over the years in fits and starts. It depends on the [Fabric](http://www.fabfile.org/) Python 3.x high-level module. It mostly does not use the host-level command and configuration options, however, because... it doesn't.

## Installation

Checkout the latest version of this repo into a Python 3 virtual environment. Use the included requirements.txt file to download and install the required modules with pip. (Below assumes a bash/zsh shell on Linux/MacOS; installation on Windows is similar but commands will differ slightly.)

```bash
~> git clone https://github.com/mbeland/naga.git
~> python3 -m venv naga
~> cd naga
~/naga> source bin/activate
(naga) ~/naga> pip install -r requirements.txt
```

## Usage

So... at the moment, the main interface is to run the file "naga.py" and specify either a hostname or "all". There's an optional parameter to specify a SQLite3 database file as well which contains the host definitions. When executed, the script will run the appropriate functions (all contained in the admin.py file) against the specified host or against all defined hosts in the database.

There are functions in the naga.py file to add/delete/modify host records, specify new app functions, etc. However at the moment these are accessed through importing the naga.py file to the interactive Python interpreter. There's a plan for changing that, but it's still just a plan.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
