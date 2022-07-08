
import jinja2
import yml_parse
import filegenerators

DIR_TEMPLATES = 'templates'


class DockerComposeFileSplitter:
    def __init__(self, docker_yml):
        self.service_yml = yml_parse.parse_service(yml_parse.load_yaml(docker_yml))
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(DIR_TEMPLATES))

    def generate_files(self):
        self.GENERATORS = [
            filegenerators.HostnameFileGenerator,
            filegenerators.PortsFileGenerator,
            filegenerators.NetmodeFileGenerator,
            filegenerators.AppFileGenerator,
        ]

        env_vars = []

        for gen in self.GENERATORS:
            if gen.needs_generation(self.service_yml):
                generator = gen(self.service_yml, self.env)
                vars = generator.generate()
                if vars:
                    env_vars.append(vars)

        for arch in yml_parse.get_image_keys(self.service_yml):
            generator = filegenerators.ImageFileGenerator(self.service_yml, self.env, arch)
            generator.generate()

        # # Generate app.yml file
        # self.service_yml['restart_variable'] = f'{self.service_yml["service_name"].upper()}_RESTART'
        # generate('app.yml', self.service_yml, None, write_queue)

if __name__ == "__main__":
    splitter = DockerComposeFileSplitter('sample_plex.yml')
    splitter.generate_files()