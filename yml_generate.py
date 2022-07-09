import click
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

        env_vars = [filegenerators.EnvVariable(f'{self.service_yml["service_name"]}_enabled', '"false"')]

        for gen in self.GENERATORS:
            if gen.needs_generation(self.service_yml):
                generator = gen(self.service_yml, self.env)
                vars = generator.generate()
                if vars:
                    env_vars += vars

        for arch in yml_parse.get_image_keys(self.service_yml):
            generator = filegenerators.ImageFileGenerator(self.service_yml, self.env, arch)
            generator.generate()

        label_gen = filegenerators.LabelsFileGenerator(self.service_yml, self.env, env_vars)
        label_gen.generate()


@click.command()
@click.argument('file', type=click.Path(exists=True))
def main(file):
    """
    Splits the docker-compose.yml into the several constituent .yml files expected for DockSTARTer apps

    FILE is the docker-compose.yml file to be split
    """
    pass
    splitter = DockerComposeFileSplitter(file)
    splitter.generate_files()

if __name__ == "__main__":
    main()
