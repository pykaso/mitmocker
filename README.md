
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
