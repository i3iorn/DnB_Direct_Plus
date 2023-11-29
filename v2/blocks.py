from enum import Enum


class DataBlock(Enum):
    businessactivityinsight = {
        "version": 1,
        "order": 1,
        "min_level": 1,
        "max_level": 3
    }
    companyfinancials = {
        "version": 3,
        "order": 2,
        "min_level": 1,
        "max_level": 4
    }
    companyinfo = {
        "version": 1,
        "order": 3,
        "min_level": 1,
        "max_level": 4
    }
    diversityinsight = {
        "version": 1,
        "order": 4,
        "min_level": 1,
        "max_level": 3
    }
    dtri = {
        "version": 1,
        "order": 5,
        "min_level": 1,
        "max_level": 3
    }
    educationaldata = {
        "version": 1,
        "order": 6,
        "min_level": 1,
        "max_level": 2
    }
    esginsight = {
        "version": 1,
        "order": 7,
        "min_level": 3,
        "max_level": 3
    }
    eventfilings = {
        "version": 1,
        "order": 8,
        "min_level": 1,
        "max_level": 3
    }
    externaldisruptioninsight = {
        "version": 1,
        "order": 9,
        "min_level": 1,
        "max_level": 4
    }
    financialstrengthinsight = {
        "version": 1,
        "order": 10,
        "min_level": 1,
        "max_level": 4
    }
    globalbusinessranking = {
        "version": 1,
        "order": 11,
        "min_level": 1,
        "max_level": 1
    }
    globalfinancials = {
        "version": 1,
        "order": 12,
        "min_level": 1,
        "max_level": 2
    }
    hierarchyconnections = {
        "version": 1,
        "order": 13,
        "min_level": 1,
        "max_level": 1
    }
    inquiryinsight = {
        "version": 1,
        "order": 14,
        "min_level": 1,
        "max_level": 4
    }
    ownershipinsight = {
        "version": 1,
        "order": 15,
        "min_level": 1,
        "max_level": 1
    }
    paymentinsight = {
        "version": 1,
        "order": 16,
        "min_level": 1,
        "max_level": 4
    }
    principalscontacts = {
        "version": 2,
        "order": 17,
        "min_level": 1,
        "max_level": 4
    }
    salesmarketinginsight = {
        "version": 2,
        "order": 18,
        "min_level": 1,
        "max_level": 3
    }
    shippinginsight = {
        "version": 1,
        "order": 19,
        "min_level": 1,
        "max_level": 1
    }
    supplychainriskindex = {
        "version": 1,
        "order": 20,
        "min_level": 1,
        "max_level": 1
    }
    thirdpartyriskinsight = {
        "version": 3,
        "order": 21,
        "min_level": 1,
        "max_level": 1
    }

    def level(self, level_int=None):
        # Only takes an int as format_spec. Make sure int is between min_level and max_level inclusive.
        if level_int is None:
            format_spec = self.value.get('min_level')
        else:
            level_int = int(level_int)
            if level_int < self.value.get('min_level'):
                raise ValueError(f"Level {level_int} is below minimum level {self.value.get('min_level')}")
            elif level_int > self.value.get('max_level'):
                raise ValueError(f"Level {level_int} is above maximum level {self.value.get('max_level')}")
        return f"{self.name}_L{level_int}_v{self.value.get('version')}"


class SideBlock(Enum):
    companyfinancials_abridged = {
        "version": 1,
        "order": 1
    }
    companyfinancials_thirdparty = {
        "version": 1,
        "order": 2
    }
    salesmarketinginsight_foottraffic = {
        "version": 1,
        "order": 3
    }
    hierarchyconnections_alternative = {
        "version": 1,
        "order": 4
    }
    hierarchyconnections_eli = {
        "version": 1,
        "order": 5
    }
    companyinfo_advgeoposition = {
        "version": 1,
        "order": 6
    }

    def __str__(self):
        return f"{self.name}_v{self.value.get('version')}"
