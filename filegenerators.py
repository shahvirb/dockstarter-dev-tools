from dataclasses import dataclass
import pathlib
import ruamel.yaml
import io
import sys

TEMPLATE_YML_PORTS = 'app.ports.yml'
TEMPLATE_YML_NETMODE = 'app.netmode.yml'
TEMPLATE_YML_HOSTNAME = 'app.hostname.yml'
TEMPLATE_YML_IMAGE = 'app.image.yml'
TEMPLATE_YML_BASE = 'app.yml'
TEMPLATE_YML_LABELS = 'app.labels.yml'


def sort_yaml(d):
    # https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys
    if isinstance(d, dict):
        res = dict()
        for k in sorted(d.keys()):
            res[k] = sort_yaml(d[k])
        return res
    if isinstance(d, list):
        return sorted(d)
    return d


def gen_yml(template, filename, service_yml, env):
    template_file = env.get_template(template)
    contents = template_file.render(service_yml)

    # Using ruamel.yaml to preserve quotes
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=2, offset=2)
    yaml.preserve_quotes = True
    data = yaml.load(contents)
    data = sort_yaml(data)
    buffer = io.BytesIO()
    yaml.dump(data, buffer)
    contents = buffer.getvalue()

    print(f'Generating {filename}')
    print('--------------------------')
    yaml.dump(data, sys.stdout)
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

    def write(self, write_dir):
        filepath = pathlib.Path(write_dir) / self.filename
        print(f'Writing {filepath}')
        with open(filepath, 'wb') as file:
            file.write(self.contents)


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
        # TODO we also need to merge in other yml contents written by the user in the compose file


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


def port_env_vars(port_mappings, service_name):
    vars = []
    for mapping in port_mappings:
        left, right = mapping.split(':')
        name = f'{service_name.upper()}_PORT_{right}'
        vars.append(EnvVariable(name, left))
    return vars


class PortsFileGenerator(FileGenerator):
    def __init__(self, service_yml, jinja_env):
        super().__init__(service_yml, jinja_env)
        self.set_filename('ports')
        self.template_file = TEMPLATE_YML_PORTS

    @classmethod
    def needs_generation(cls, service_yml):
        return bool(len(service_yml['ports']))

    def generate(self):
        env_vars = port_env_vars(self.service_yml['ports'], self.service_yml['service_name'])
        render_vars = self.service_yml
        render_vars['port_vars'] = env_vars
        super().generate(render_vars)
        # Revise all the env_vars values now so that the port numbers are strings. eg 80 -> "80"
        for ev in env_vars:
            ev.value = f'"{ev.value}"'
        return env_vars


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
        #TODO we also need to merge in other labels written by the user in the compose file
