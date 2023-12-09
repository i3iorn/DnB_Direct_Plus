import json
import math
from pathlib import Path

from v2 import API_CREDENTIALS
from v2.direct_plus import DirectPlus
from v2.search_criteria import SearchCriteriaManager

# Constants
REFERENCE_DATA_ID = 3599
COUNTRY_ISO_ALPHA2_CODE = 'US'
POSTAL_CODE = '77024'
CHUNK_SIZE_MODIFIER = 10

# Initialize Direct+ API
dp = DirectPlus(
    API_CREDENTIALS.get('personal').get('test'),
    'ALLOW_INTERNAL',
    'ALLOW_TRIAL',
    'PRODUCTION'
)

refs = dp.call(
    'refdataCodes',
    id=REFERENCE_DATA_ID
).json()
codes = [ref.get('code') for ref in refs.get('codeTables')[0].get('codeLists')]


scg = SearchCriteriaManager(
    dp,
    countryISOAlpha2Code=COUNTRY_ISO_ALPHA2_CODE,
    postalCode=POSTAL_CODE,
    isOutOfBusiness=False,
    pageNumber=20,
    pageSize=50,
    industryCodes=[
        {
            'code': codes,
            'typeDnbCode': 3599
        }
    ],
)

print(scg.get_hits())
