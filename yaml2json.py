import argparse
import yaml
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', type=argparse.FileType('r'))
    parser.add_argument('json_file', type=argparse.FileType('w'))
    args = parser.parse_args()

    args.json_file.write(json.dumps(yaml.safe_load(args.yaml_file)))


main()
