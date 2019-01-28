
from mitmocker import mock, MitmMockServer
# 'mock' is wrapper function
# It takes two positional parameters:
#  - first - URL or mask (reqular expression)
#  - second (optional) - method type, default is 'GET'
# 'MitmMockServer' is base server class which should be inherited 

import os
from random import uniform



class MockExample1(MitmMockServer): 

    def __init__(self):
        super().__init__(os.path.dirname(os.path.realpath(__file__)))

        # in first version, used only to crop long filenames for stored responses
        self.baseUrl = '/mobile/v1/'

        # ------- custom variables -------- #
        # It's possible to store any variable that could be used in PJSON files
        self.availableBalance = round(uniform(199, 2999), 2)

    # In this case is mock function applied to any request starts with '/mobile/v1/'
    # All matching responses are stored to 'data' folder as files named by request path with extension 'pjson'
    @mock('/mobile/v1/')
    def mock_all(self, flow):
        # get_template() takes optional parameter "name" of PJSON file in "data" directory
        return self.get_template()


addons = [
    MockExample1()
]