from dataclasses import dataclass
import jinja2
import yml_parse

DIR_TEMPLATES = 'templates'

@dataclass()
class WriteFile:
    name: str
    contents: str

    def write(self):
        pass


class DockerComposeFileSplitter:
    def __init__(self, docker_yml):
        self.service_yml = yml_parse.parse_service(yml_parse.load_yaml(docker_yml))
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(DIR_TEMPLATES))

    def generate_files(self):
        write_queue = []

        def generate(template, service_yml, filetype, write_queue):
            template_file = self.env.get_template(template)
            contents = template_file.render(self.service_yml)
            filename = f'{service_yml["service_name"]}.{filetype}.yml' if filetype else f'{service_yml["service_name"]}.yml'
            print(f'Generating {filename}')
            print(contents)
            write_queue.append(WriteFile(filename, contents))

        # Generate image files
        image_types = yml_parse.get_image_keys(self.service_yml)
        for type in image_types:
            generate('app.image.yml', self.service_yml, type, write_queue)

        # Generate ports file
        if len(self.service_yml['ports']):
            generate('app.ports.yml', self.service_yml, 'ports', write_queue)

        # Generate netmode file
        self.service_yml['netmode_variable'] = f'{self.service_yml["service_name"].upper()}_NETWORK_MODE'
        generate('app.netmode.yml', self.service_yml, 'netmode', write_queue)

        # Generate hostname file
        generate('app.hostname.yml', self.service_yml, 'hostname', write_queue)

        # Generate app.yml file
        self.service_yml['restart_variable'] = f'{self.service_yml["service_name"].upper()}_RESTART'
        generate('app.yml', self.service_yml, None, write_queue)

if __name__ == "__main__":
    splitter = DockerComposeFileSplitter('sample_plex.yml')
    splitter.generate_files()