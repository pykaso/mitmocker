from mitmproxy import ctx
from mitmproxy import http
import json
import re
import os
import sys
import contextvars

context_flow = contextvars.ContextVar('context_flow')

# import of useful methods which could be used in pjson templates
from random import randint, uniform
from datetime import datetime, timezone, timedelta
import math

MOCKS = {}

_AUTOMOCK_QUEUE = {}
_TEMPLATE_EXTENSION = 'pjson'


def mock(url, method='GET', autocreate=True):
    def _decorator(func):
        MOCKS[url] = (method, func, autocreate)
        return func
    return _decorator

def safe_name(url):
    safe = re.sub(r'[^a-zA-Z0-9]', '_', url).replace('__', '_').lower()
    if safe.startswith('_'):
        safe = safe[1:]
    return safe

def currentFuncName(n=0):
    return sys._getframe(n + 1).f_code.co_name


class MitmMockServer(object):

    prevRequestPath = None
    baseUrl = ''
    work_dir = None
    data_dir = None

    def __init__(self, work_dir):
        self.work_dir = work_dir
        self.data_dir = os.path.join(work_dir, 'data')


    def check_dirs(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)


    def request(self, flow):
        self.check_dirs()
        self.serve_mocks(flow)
        self.prevRequestPath = flow.request.path


    def response(self, flow):
        if len(_AUTOMOCK_QUEUE.keys()) > 0:
            _to_delete = []

            for name, (url, method) in _AUTOMOCK_QUEUE.items():
                if flow.request.path == url and flow.request.method == method:
                    template_name = self._get_template_name(name)
                    template_file = os.path.join(self.data_dir, template_name)

                    with open(template_file, 'w') as template:
                        json.dump(json.loads(flow.response.text), template, indent=4, sort_keys=True, ensure_ascii=False)
                    self.log('Response of "{0}" was saved to file: {1}'.format(flow.request.path, template_file))
                    _to_delete.append(name)
                    break
        
            if len(_to_delete)>0:
                for dname in _to_delete:
                    if dname in _AUTOMOCK_QUEUE:
                        del _AUTOMOCK_QUEUE[dname]


    def get_templates(self, name):
        files = [file for file in os.listdir(self.work_dir) if file.startswith(name)]
        contents = [self._load_template(file) for file in files]
        evaluated = [self._evaluate_template(content) for content in contents]
        objects = [json.loads(content) for content in evaluated]
        return objects


    def get_template(self, name=None):
        caller = currentFuncName(1)
        meta = self._find_meta(caller)
        if not meta:
            raise Exception('Invalid meta info')
        method, _, autocreate = meta

        _flow = context_flow.get()
        if name is None:
            default_template_name = _flow.request.path.replace(self.baseUrl, '')
            name = safe_name(default_template_name)

        template_name = self._get_template_name(name)
        template_file = os.path.join(self.data_dir, template_name)

        self.warn('get_template: name={0}, meta={1}'.format(name, meta))

        if os.path.exists(template_file):
            content = self._load_template(template_file)
            evaluated = self._evaluate_template(content)
            obj = json.loads(content)
            self.log('Response to "{0}" served from mock file "{1}".'.format(_flow.request.path, template_file))
            return obj
        else:
            if autocreate == False:
                self.warn('Template file "{0}" not found. Mock file autocreate is disabled.')
                return None
            else:
                _AUTOMOCK_QUEUE[name] = (_flow.request.path, method)


    def json_response(self, body):
        return http.HTTPResponse.make(200, json.dumps(body), {"Content-Type": "application/json"})


    def is_url_match(self, flow, url):
        if flow.request.path == url:
            return True
        if re.search('^{0}'.format(url), flow.request.path):
            return True
        return False


    def serve_mocks(self, flow):
        def call(content):
            if content:
                flow.response = self.json_response(content)

        for url, (method, func, autocreate) in MOCKS.items():
            if self.is_url_match(flow, url) and flow.request.method == method:
                token = context_flow.set(flow)
                content = func(self, flow)
                context_flow.reset(token)
                call(content)
                return


    def match_func(self, match):
        try:
            expression = match.group(2)

            if len(expression) == 0:
                raise Exception('Expression can\'t be empty.')

            if '||' in expression:
                expression, variable =  expression.split('||')
            else:
                variable = None

            self.log('Expression detected: "{0}"'.format(expression))
            if variable:
                self.log('Store expression result to variable named: "{0}"'.format(variable))

            if '$' in expression:
                variables = [ var[1:] for var in re.findall(r'\$[a-zA-Z]+', expression)]
                if len(variables)>0:
                    self.log('Named variables detected : {0}'.format(variables))

                    for variable_name in variables:
                        stored_variable = None
                        
                        if hasattr(self, variable_name):
                            stored_variable = getattr(self, variable_name)
                        elif variable_name in globals():
                            stored_variable = globals()[variable_name]

                        if stored_variable:
                            #self.log('found existing variable "{0}"'.format(stored_variable))
                            expression = expression.replace('${0}'.format(variable_name), '{0}'.format(stored_variable))
                        else:
                            self.log('Variable name {0} not defined in object or globals.'.format(variable_name))

                    #self.log('variables replaced : {0}'.format(expression))            
        
            try:
                expression = str(expression)
                evaluated = eval(expression)
                #self.log('Expression evaluated: {0}'.format(evaluated))
            except Exception as e :
                raise Exception('Expression evaluation failed with error: {0}'.format(e))
                evaluated = expression

            if variable:
                globals()[variable] = evaluated

            return "{0}".format(evaluated)

        except Exception as e:
            self.warn('Failed to evaluate expression "{0}". Error: {1}'.format(match.group(), e))


    def json_prettyprint(self, data):
        return simplejson.dumps(simplejson.loads(data), indent=4, sort_keys=False)


    def _get_template_name(self, name):
        return '{0}.{1}'.format(name, _TEMPLATE_EXTENSION)


    def _load_template(self, filename):
        with open(filename) as f:
            return f.read()


    def _evaluate_template(self, templateContent):
        replaced = re.sub(r'(\{\{)([^}]+)(\}\})', self.match_func, templateContent)
        return replaced


    def _find_meta(self, func_name):
        result = {k: v for k, v in MOCKS.items() if v[1].__name__ == func_name}
        if len(result):
            key = list(result.keys())[0]
            return result[key]

    
    def log(self, message):
        ctx.log.info(message)

    
    def warn(self, warning):
        ctx.log.warn(warning)


