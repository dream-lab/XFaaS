import os
from jinja2 import Environment, FileSystemLoader


# TODO - add custom exception class

def get_template_file(trigger_type="placeholder"):
    return "orchestrator_template.py"

def generate(code, template_dir, output_dir):
    # generating templates
    try:
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader)
        template = env.get_template(get_template_file()) # TODO - place trigger type here
    except Exception as exception:
        raise Exception("Error in loading jinja template environment",exception)
    
    # render function
    try:
        output = template.render(code=code)
    except Exception as exception:
        raise Exception("Error in jinja template render function",exception)

    try:
        # flush out the generator yaml
        # TODO - make the .py filename as a parameter (configurable)
        with open(f"{output_dir}/orchestrator.py", "w+") as _sfn_yaml:
            _sfn_yaml.write(output)
    except Exception as exception:
        raise Exception("Error in writing to template file",exception)
        