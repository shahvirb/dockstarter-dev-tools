from dataclasses import dataclass

TEMPLATE_YML_PORTS = 'app.ports.yml'
TEMPLATE_YML_NETMODE = 'app.netmode.yml'
TEMPLATE_YML_HOSTNAME = 'app.hostname.yml'
TEMPLATE_YML_IMAGE = 'app.image.yml'
TEMPLATE_YML_BASE = 'app.yml'
TEMPLATE_YML_LABELS = 'app.labels.yml'

def gen_yml(template, filename, service_yml, env):
    template_file = env.get_template(template)
    contents = template_file.render(service_yml)
    print(f'Generating {filename}')
    print('--------------------------')
    print(contents)
    print('--------------------------')
    return contents


@dataclass
class EnvVariable:
    name: str
    value: str


class FileGenerator:
    def __init__(self, service_yml, jinja_env):
        self.service_yml = service_yml
        self.env = jinja_env
        self.filename = None
        self.contents = None
        self.template_file = None

    @classmethod
    def needs_generation(cls, service_yml):
        return True

    def generate(self, render_vars=None):
        if not render_vars:
            render_vars = self.service_yml
        self.contents = gen_yml(self.template_file, self.filename, render_vars, self.env)
        return None

    def set_filename(self, type=None):
        self.filename = self.service_yml["service_name"] + (f'.{type}.yml' if type else f'.yml')

    def write(self):
        raise NotImplementedError


class AppFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename(None)
        self.template_file = TEMPLATE_YML_BASE

    def generate(self):
        restart_var = EnvVariable(f'{self.service_yml["service_name"].upper()}_RESTART', 'unless-stopped')
        render_vars = self.service_yml
        render_vars['restart_variable'] = restart_var.name
        super().generate(render_vars)
        return [restart_var]


class HostnameFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('hostname')
        self.template_file = TEMPLATE_YML_HOSTNAME


class ImageFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env, arch):
        super().__init__(service_yml, jinja_env)
        self.arch = arch
        self.set_filename(arch)
        self.template_file = TEMPLATE_YML_IMAGE

    def generate(self):
        render_vars = self.service_yml
        render_vars["image_arch"] = self.service_yml[f'image_{self.arch}']
        super().generate(render_vars)


class NetmodeFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('netmode')
        self.template_file = TEMPLATE_YML_NETMODE

    def generate(self):
        mode_var = EnvVariable(f'{self.service_yml["service_name"].upper()}_NETWORK_MODE', '""')
        render_vars = self.service_yml
        render_vars['netmode_variable'] = mode_var.name
        super().generate(render_vars)
        return [mode_var]


class PortsFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('ports')
        self.template_file = TEMPLATE_YML_PORTS

    @classmethod
    def needs_generation(cls, service_yml):
        return bool(len(service_yml['ports']))


class LabelsFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env, env_vars):
        super().__init__(service_yml, jinja_env)
        self.set_filename('labels')
        self.template_file = TEMPLATE_YML_LABELS
        self.env_vars = env_vars

    def generate(self):
        render_vars = self.service_yml
        render_vars['env_vars'] = self.env_vars
        super().generate(render_vars)
