pycrcmanip
========
A command line interface tool that lets you reverse and freely change CRC
checksums through smart file patching.

This is a modified version of [pycrcmanip](https://github.com/rr-/pycrcmanip) that compiles.
Changes made:
- Refactored tool to not be a module anymore (Removed dependency on poetry)
- Fixed fastcrc.c overflow errors.

## Setup
```bash
python -m venv venv # Install in a venv (optional)
./venv/Scripts/activate

pip install -r requirements.txt
python setup.py build_ext --inplace
```
## Run Example
```bash
python ./main.py patch -a CRC32 -O -P -4 ./ExcelDB.db $(python ./main.py calc -q -a CRC32 ./ExcelDB_original.db)
```