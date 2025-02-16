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
with open('./output/LocalizeEtcExcelTable.json', 'wb') as f:
    f.write(json.dumps(tbxt.bytes2json(Path('./input/LocalizeEtcExcelTable.bytes')), indent=4, ensure_ascii=False).encode('utf8'))
"""
from extractor import TablesExtractor
TablesExtractor('JPExtracted', './input/TablesRaw').extract_tables()