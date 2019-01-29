
# mitmocker
Mock server for [MITM](https://mitmproxy.org/) proxy
Developed with a focus on two main points:
1. Automatic recording API response for the first request.
2. Support scripting in JSON templates.

## Requirements
Mitmocker is a mock server for MITM. Installation of MITM seems to be a good starting point.
    
    brew install mitmproxy

## Instalation

    pip install git+https://github.com/pykaso/mitmocker

## Usage

1. Create a python script with mock server using MITM scripting API.


        from mitmocker import mock, MitmMockServer
        import os

        class MinimalMockServer(MitmMockServer): 

            def __init__(self):
                super().__init__(os.path.dirname(os.path.realpath(__file__)))

            @mock('/api/v1/')
            def mock_all(self, flow):
                return self.get_template()

        addons = [
            MinimalMockServer()
        ]


2. Run MITM in reverse mode with a created script. This starts the proxy on localhost and default port 8080.


        mitmproxy -s ./mobilemock.py --mode reverse:http://api.servi.ce


In this minimal configuration, every first response of request starting with '/api/v1/' is recorded to single file in 'data' subdirectory in the current working directory. When same request is fired and coresponding file exists, the mock server responds with stored file. Point your application to running proxy and start using *automagic* mocks.

## Response modification

Response could be modified in many ways. For example by direct modification of object returned from `get_template()` function. If conditional response is needed, it's also possible to use a build-in property `prevRequestPath` or create a custom one.

    @mock('/mobile/v1/marketplace/loans/([0-9]+)')
    def loan(self, flow):
        loan = self.get_template()

        # test for previous request path
        if self.prevRequestPath == '/mobile/v1/marketplace/reservations/my-reservations':
            # direct template modification
            loan['my-reservations'] = {
                'custom': 'value'
            }
        return loan

Another way is defining variable right in `pjson` file by closing the name beginning with the `$` character between brackets. For example: `{{$customVariable}}`. The value for the variable defined like this is searched first in the mock server instance variable or in global variables.

In the brackets can be also used python expression like: `{{random(1, 100)}}`

Result of expression in `pjson` file could be stored to variable by this simple syntax: `{{random(1, 100)||localVariable}}`.

In this example, the expression is evaluated and the result is stored to a global variable named `localVariable` which is used later on the next line.

    {
        "balance": {{round(uniform(100, 10000), 2)||localVariable}},
        "balanceRounded": {{round($localVariable)}}
    }

