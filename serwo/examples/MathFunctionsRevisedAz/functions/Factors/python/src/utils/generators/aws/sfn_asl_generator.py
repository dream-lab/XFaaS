import aws_sfn_builder as AWSSfnBuilder


def generate_statemachine_json(statemachine_structure, output_dir, output_file):
    # TODO - include the branching via networkx as a parameter
    sfn_json = AWSSfnBuilder.Machine.parse(statemachine_structure).to_json()

    # write to output directory
    with open(f"{output_dir}/{output_file}", "w") as statemachinejson:
        statemachinejson.write(sfn_json)
