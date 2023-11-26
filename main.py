from v2 import API
from v2.direct_plus import DirectPlus

dp = DirectPlus(API['key'], API['secret'], 'ALLOW_INTERNAL', 'ALLOW_TRIAL', 'PRODUCTION')

# print(dp.entitlements)

# print(dp.call_endpoint('dataBlocks', dunsNumber='352539722', blockIDs='companyinfo_L1_v1').json())
# print(dp.accesible_data_blocks_and_products)
print(dp.get_all_avaiable_data_for_duns('352539722'))
