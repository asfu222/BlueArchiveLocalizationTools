#from extractor import compile_python
#compile_python("./input/dump.cs", "./JPExtracted")
"""
from repacker import TableRepackerImpl
import os
from pathlib import Path
if not os.path.exists('output'):
    os.makedirs('output')
packer = TableRepackerImpl('JPExtracted.FlatData')
with open('./output/AcademyMessanger1ExcelTable.bytes', 'wb') as f:
    f.write(packer.repackExcelZipJson(Path('./input/AcademyMessanger1ExcelTable.json')))
"""
"""

from extractor import TableExtractorImpl
import os
from pathlib import Path
import json
if not os.path.exists('output'):
    os.makedirs('output')
tbxt = TableExtractorImpl('JPExtracted.FlatData')
with open('./output/AcademyMessanger1ExcelTable_modified.json', 'wb') as f:
    f.write(json.dumps(tbxt.bytes2json(Path('./output/AcademyMessanger1ExcelTable.bytes')), indent=4, ensure_ascii=False).encode('utf8'))
"""