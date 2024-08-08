import re
import os


# def serwolist_to_obj(var):
#     list = var.get_objects()
#     # matadata=var.get_metadata()
#     List = []
#     for obj in list:
#         body = obj.get_body()
#         List.append(body)
#     return list

def map_cod_gen(lists, name):
    first_obj = lists[0]
    new_code = 'serwo_to_dict = unmarshall(json.loads(' + \
        first_obj[2] + '))\n'
    new_code += 'body = serwo_to_dict.get_body()\n'
    new_code += 'obj = body["' + name + '"]\n'
    new_code += 'std_meta = serwo_to_dict.get_metadata()\n'

    for i in range(0, len(lists)):
        new_code += lists[i][0] + ' = []\n'
    new_code += '\nfor i in range(0, len(obj)):\n'
    new_code += 'var = {' + '"body": obj[i], "metadata": std_meta }\n'
    new_code += 'var = build_serwo_object(var).to_json()\n'
    new_code +=  \
        first_obj[0] + \
        '.append(context.call_activity(' + first_obj[1]+' , var))\n'

    for i in range(1, len(lists)):
        l = lists[i]
        new_code +=  \
            l[0]+'.append(context.call_activity(' + \
            l[1]+' , ' + l[2] + '[i]))\n'
    
    # this is out of for loop
    lines = new_code.split('\n')
    indented_lines = ['\n\t' + lines[i] for i in range(0,len(lines)-1)]
    # print(indented_lines)
    
    last_obj = lists[-1]
    last_code = []
    last_code.append("\n")
    last_code.append("\n    "+last_obj[0]+' = yield context.task_all('+last_obj[0]+')')
    last_code.append("\n    "+'body["'+name + \
        '"+"results"] = serwolist_to_obj('+last_obj[0] + ')')
    last_code.append('\n    var2 = {' + '"body": body, "metadata": std_meta }')
    last_code.append("\n    "+last_obj[0] + ' = build_serwo_object(var2).to_json()')
    last_code.append('\n')

    # print(lines)
    indented_lines+=['\n']+last_code

    # print(indented_lines)
    return indented_lines

def extract_var(input_str):
    # Define the regular expressions
    variable_regex = r'^\s*([a-zA-Z_]\w*)\s*='
    function_call_regex = r'\bcontext\.call_activity\(\s*"([^"]*)"\s*,\s*([^)]*)\)'

    # Extract the variable name and function call arguments
    variable_match = re.match(variable_regex, input_str)
    variable_name = variable_match.group(1) if variable_match else None

    # Extract function call arguments
    function_call_match = re.search(function_call_regex, input_str)
    if function_call_match:
        first_argument = function_call_match.group(1)
        second_argument = function_call_match.group(2)
    else:
        first_argument = None
        second_argument = None
    first_argument = '"'+str(first_argument)+'"'
    # print("Variable Name:", variable_name)
    # print("First Argument:", first_argument)
    # print("Second Argument:", second_argument)
    return [str(variable_name), first_argument, str(second_argument)]

class map_update:
    def add_graph_node(inpath, outpath, subgraphs):
        if subgraphs == None:
            return
        with open(inpath, 'r') as file_ptr:
            lines = file_ptr.readlines()
        str = "context.call_activity"
        new_lines = []
        for subgraph in subgraphs:
            i = 0
            list_subgraphs = []
            # print(len(lines))
            while i<len(lines):
                line = lines[i]
                if str in line and subgraph["Nodes"][0] in line:
                    for j in range(0, len(subgraph["Nodes"])):
                        line = lines[i+j]
                        var = extract_var(line)
                        list_subgraphs.append(var)
                    new_map_code = map_cod_gen(list_subgraphs, subgraph["Listname"])
                    new_lines.append(new_map_code)
                    i = i+len(subgraph["Nodes"])
                else:
                    new_lines.append(lines[i])
                    i+=1
                # print("i",i)    
        # print(new_lines)
        with open(outpath, 'w') as file_ptr:
            for line in new_lines:
                file_ptr.write("".join(line))
        os.system(f"autopep8 --in-place {outpath}")


# l=[
#     ['ehzx','"Splitter"','serwoObject'],
#     ['abcd','"Transpiler"','ehzx'],
#     ['efgh','"Submitter"','abcd']
# ]

# print(map_cod_gen(l,"list"))
