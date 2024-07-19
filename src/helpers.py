import yaml

def read_config(yaml_file_path):
    with open(yaml_file_path, 'r') as file:
        input_data_fmt = yaml.safe_load(file)
    return input_data_fmt

def readline(fn, line):
    """Read individual line from a file."""
    with open(fn, 'r') as file:
        lines = file.readlines()
    return lines[line]