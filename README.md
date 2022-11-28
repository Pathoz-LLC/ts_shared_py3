# ts_shared_py3
contains shared models, messages, enums and constants for various ts microservices

#### to validate deps
python src/main_validate.py


#### to install from github
python3 -m pip install -e git+https://github.com/Pathoz-LLC/ts_shared_py3.git#egg=ts_shared_py3


##### dev setup
python3 -m venv tsSharedEnv
menu:   View -> Command Palette -> Select Python Interptreter  (pick from tsSharedEnv)
menu:   Terminal -> New Terminal
python -m pip install --upgrade pip
pip install -r requirements.txt


#### grpcio install on M1 mac
pip uninstall grpcio
export GRPC_PYTHON_LDFLAGS=" -framework CoreFoundation"
pip install grpcio --no-binary :all:


##### misc pip installer
python -m pip install flask
pip freeze > requirements.txt


#### to build for pypy
python3 -m pip install --upgrade build

from here:
https://packaging.python.org/en/latest/tutorials/packaging-projects/