from abc import ABC

TEMPLATE_YML_PORTS = 'app.ports.yml'
TEMPLATE_YML_NETMODE = 'app.netmode.yml'
TEMPLATE_YML_HOSTNAME = 'app.hostname.yml'
TEMPLATE_YML_IMAGE = 'app.image.yml'

def gen_yml(template, filename, service_yml, env):
    template_file = env.get_template(template)
    contents = template_file.render(service_yml)
    print(f'Generating {filename}')
    print('--------------------------')
    print(contents)
    print('--------------------------')


class FileGenerator:
    def __init__(self, service_yml, jinja_env):
        self.service_yml = service_yml
        self.env = jinja_env
        self.filename = None
        self.contents = None

    @classmethod
    def needs_generation(cls, service_yml):
        return True

    def generate(self):
        raise NotImplementedError

    def set_filename(self, type=None):
        self.filename = self.service_yml["service_name"] + f'.{type}.yml' if type else f'.yml'

    def write(self):
        raise NotImplementedError

class HostnameFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('hostname')

    def generate(self):
        gen_yml(TEMPLATE_YML_HOSTNAME, self.filename, self.service_yml, self.env)

class ImageFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env, arch):
        super().__init__(service_yml, jinja_env)
        self.arch = arch
        self.set_filename(arch)

    def generate(self):
        render_vars = self.service_yml
        render_vars["image_arch"] = self.service_yml[f'image_{self.arch}']
        gen_yml(TEMPLATE_YML_IMAGE, self.filename, self.service_yml, self.env)


class NetmodeFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('netmode')

    def generate(self):
        # TODO should this really be stored back into the service_yml or just some render_vars that is passed to gen_yml
        self.service_yml['netmode_variable'] = f'{self.service_yml["service_name"].upper()}_NETWORK_MODE'
        gen_yml(TEMPLATE_YML_NETMODE, self.filename, self.service_yml, self.env)
        # TODO what if we append some sort of label_vars list with the variable name we just created


class PortsFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('ports')

    @classmethod
    def needs_generation(cls, service_yml):
        return bool(len(service_yml['ports']))

    def generate(self):
        gen_yml(TEMPLATE_YML_PORTS, self.filename, self.service_yml, self.env)
