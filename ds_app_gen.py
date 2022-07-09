import click
import jinja2
import yml_parse
import filegenerators

DIR_TEMPLATES = 'templates'


class DockerComposeFileSplitter:
    def __init__(self, docker_yml):
        self.service_yml = yml_parse.parse_service(yml_parse.load_yaml(docker_yml))
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(DIR_TEMPLATES))
        self.generators_run = []

    def generate_files(self):
        self.GENERATOR_TYPES = [
            filegenerators.HostnameFileGenerator,
            filegenerators.PortsFileGenerator,
            filegenerators.NetmodeFileGenerator,
            filegenerators.AppFileGenerator,
        ]

        env_vars = [filegenerators.EnvVariable(f'{self.service_yml["service_name"]}_enabled', '"false"')]

        self.generators_run = []

        for gen in self.GENERATOR_TYPES:
            if gen.needs_generation(self.service_yml):
                generator = gen(self.service_yml, self.env)
                self.generators_run.append(generator)
                vars = generator.generate()
                if vars:
                    env_vars += vars

        for arch in yml_parse.get_image_keys(self.service_yml):
            generator = filegenerators.ImageFileGenerator(self.service_yml, self.env, arch)
            self.generators_run.append(generator)
            generator.generate()

        label_gen = filegenerators.LabelsFileGenerator(self.service_yml, self.env, env_vars)
        self.generators_run.append(label_gen)
        label_gen.generate()

    def write(self, output_dir):
        for g in self.generators_run:
            g.write(output_dir)


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--dry_run/--write', default=True, help='dry_run (default) indicates no output files are written. Use write to write output files.')
@click.option('--output_dir', default=None, type=click.Path(exists=True), help='output directory to write files into. If not provided writes file in current working directory.')
def main(file, dry_run, output_dir):
    """
    Splits the docker-compose.yml into the several constituent .yml files expected for DockSTARTer apps

    FILE is the docker-compose.yml file to be split
    """

    splitter = DockerComposeFileSplitter(file)
    splitter.generate_files()

    if not dry_run:
        if not output_dir:
            import pathlib
            output_dir = pathlib.Path.cwd()
        splitter.write(output_dir)


if __name__ == "__main__":
    main()
