from v2 import API_CREDENTIALS
from v2.direct_plus import DirectPlus

dp = DirectPlus(
    API_CREDENTIALS.get('personal').get('test'),
    'ALLOW_INTERNAL',
    'ALLOW_TRIAL',
    'PRODUCTION'
)
"""
print(dp._call_endpoint(
    'refdataCategories',
).json())
quit()
"""
reference = dp._call_endpoint(
    'refdataCodes',
    id=3599
)
"""
print(reference.json().get('codeTables')[0].get('codeLists'))
"""
codes = []
for cd in reference.json().get('codeTables')[0].get('codeLists'):
    try:
        cdr = {
            'code': cd['code'],
            'description': cd['description'],
            'typeDnbCode': 3599
        }
        codes.append(cdr)
    except KeyError:
        print(cd)
        quit()

print(dp.search_by_criteria(
    industryCodes=codes,
    countryISOAlpha2Code='US',
    postalCode='77024',
))
