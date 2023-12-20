import re
import csv
import json
import random
from collections import Counter
from pathlib import Path
from time import perf_counter

from src import API_CREDENTIALS
from src.direct_plus import DirectPlus
from src.exceptions import DunsException
from src.transformer import Transformer

# Initialize Direct+ API
dp = DirectPlus(
    API_CREDENTIALS.get('personal').get('test'),
    'ALLOW_INTERNAL',
    'ALLOW_TRIAL',
    'PRODUCTION'
)

results = []
with open(r"C:\Users\schrammelb\Downloads\Arbmapp - Björn\IQ Single File Nordic New  - OM.out.tsv", "r", encoding="UTF8") as csv_file:
    duns_list = [line.split('\t')[1] for line in csv_file.readlines() if re.fullmatch(r'[0-9]{1,9}', line.split('\t')[1])]
    for duns in duns_list[:20]:
        try:
            result: dict = dp.enrich_duns(
                    duns=str(duns),
                    blockIDs='companyinfo_L1_v1'
            ).get('organization', {}).get('countryISOAlpha2Code')
        except DunsException as e:
            continue
        results.append(result)

    print(Counter(results))
"""
data_processor = Transformer(results)
data_processor.export_to_csv(f"results.csv", overwrite=True)
"""