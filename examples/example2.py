
from mitmocker import mock, MitmMockServer
import os
from random import uniform



class MockExample2(MitmMockServer): 

    def __init__(self):
        super().__init__(os.path.dirname(os.path.realpath(__file__)))

        # It's possible to store any variable that could be used also in PJSON files
        self.customVariable = ''

    # In this case is mock function applied to any request matching regular expression
    @mock('/mobile/v1/marketplace/loans/([0-9]+)')
    def loan(self, flow):
        loan = self.get_template()

        self.customVariable = 'default_value'

        # test for previous request path
        if self.prevRequestPath == '/mobile/v1/marketplace/reservations/my-reservations':
            # modify custom variable
            self.customVariable = 'matching'

            # direct template modification
            loan['my-reservations'] = {
                'custom': 'dict'
            }

        return loan

addons = [
    MockExample2()
]
