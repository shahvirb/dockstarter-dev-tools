from ruamel import yaml


def load_yaml(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def parse_service(yaml):
    if 'services' not in yaml:
        raise KeyError('services not found in yaml file')
    if len(yaml['services']) != 1:
        raise NotImplementedError('services has more on than one service defined. This utility only supports one service')

    # we should only have one service so the first key is the service
    service_name = next(iter(yaml['services']))
    parsed = yaml['services'][service_name]
    parsed['service_name'] = service_name
    return parsed

def get_image_keys(service_yml):
    return [k.split('image_')[-1] for k in service_yml.keys() if k.startswith('image_')]

if __name__ == "__main__":
    print(parse_service(load_yaml('sample_plex.yml')))