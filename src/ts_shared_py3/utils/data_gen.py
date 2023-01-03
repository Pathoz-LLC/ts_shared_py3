import yaml
from random import randint  # for mock data

# usage:
# from ts_shared_py3.utils.seed_data import forRowInYaml


def forRowInYaml(relFilePath, funcToRun):
    """process yaml file using passed function"""
    yamlRows = []
    with open(relFilePath) as f:  # service_backend/dialog/
        try:
            yamlRows = yaml.safe_load(f)
            # yamlRows = fileAsDict.get('questions')
        except yaml.YAMLError as exc:
            print(exc)
            raise

    # print('yamlRows:')
    # print(yamlRows)
    results = []
    for rec in yamlRows:
        results.append(funcToRun(rec))
    return results


def randIntInRange(min=0, max=2):
    return randint(min, max)
