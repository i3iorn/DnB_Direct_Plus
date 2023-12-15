import csv
from pathlib import Path
from time import perf_counter

from src import API_CREDENTIALS
from src.direct_plus import DirectPlus
from src.transformer import Transformer

# Initialize Direct+ API
dp = DirectPlus(
    API_CREDENTIALS.get('personal').get('test'),
    'ALLOW_INTERNAL',
    'ALLOW_TRIAL',
    'PRODUCTION'
)

results = []
duns_list = ['118998879', '006990569', '078610275']
for duns in duns_list:
    result: dict = dp.enrich_duns(
            duns=duns,
            blockIDs='companyinfo_L2_v1,principalscontacts_L1_v2'
    ).get('organization', {})

    results.append(result)

data_processor = Transformer(results)
data_processor.export_to_csv(f"results.csv", overwrite=True)

# print(json.dumps(dp.call('elifft', duns='118998879', productId='elifft', versionId='v1').json(), indent=4))
