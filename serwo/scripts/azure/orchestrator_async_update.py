import re
import os

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
    first_argument='"'+str(first_argument)+'"'
    # print("Variable Name:", variable_name)
    # print("First Argument:", first_argument)
    # print("Second Argument:", second_argument)
    return str(variable_name), first_argument, str(second_argument)

def async_codegen(in_var,out_var,func_name):
    # new_code ='\n'
    # new_code ='\n\t'+ out_var +' = '+ in_var
    # new_code +='\n\twhile True: '
    # new_code +='\n\t\t' + out_var + ' = ' + 'yield context.call_activity(' + func_name + ','+ out_var +')'
    # new_code +='\n\t\tbody = unmarshall(json.load(' + out_var + ')).get_body() ' 
    # new_code +='\n\t\tif "results" in body["data"]: '
    # new_code +='\n\t\t\tbreak '
    # new_code +='\n\t\tdeadline = context.current_utc_datetime + timedelta(miniutes=15) '
    # new_code +='\n\t\tyield context.create_timer(deadline)\n\n'
    new_code ='\n'
    new_code +='\n\t'+ out_var +' = '+ in_var
    new_code +='\n\twhile True: '
    new_code +='\n\t' + out_var + ' = ' + 'yield context.call_activity(' + func_name + ','+ out_var +')'
    new_code +='\n\tbody = unmarshall(json.loads(' + out_var + ')).get_body() ' 
    new_code +='\n\tif not body["Poll"] or body["Poll"]==False: '
    new_code +='\n\t\tbreak '
    new_code +='\n\telse:'
    new_code +='\n\t\tdeadline = context.current_utc_datetime + timedelta(seconds=900) '
    new_code +='\n\t\tyield context.create_timer(deadline)\n\n'
    return new_code

def find_var(orch_path,async_fn_name_list):
    print("Async Fn list",async_fn_name_list)
    with open(orch_path, 'r') as file_ptr:
        lines = file_ptr.readlines()
    var_set=set()
    str= "context.call_activity"
    for line in lines:
        if str in line:
            a,fn,b= extract_var(line)
            fn=fn[1:-1]
            if fn in async_fn_name_list:
                # print("Extracted variables",a,fn,b)
                var_set.add(a)

    return var_set

class async_update:
    def orchestrator_async_update(in_orchestrator_path,out_orchestrator_path,async_func_set):
        
        var_list=find_var(in_orchestrator_path,async_func_set)
        print("Var list:",var_list)
        with open(in_orchestrator_path, 'r') as file_ptr:
            lines = file_ptr.readlines()

        new_lines = []
        for line in lines:
            if 'context.call_activity' in line:
                a,b,c= extract_var(line)
                if c in var_list:
                    new_code=async_codegen(c,a,b)
                    print(new_code)
                    new_lines.append(new_code)
                else:
                    new_lines.append(line)    
            else:
                new_lines.append(line)
        # print(new_lines)
        with open(out_orchestrator_path, 'w') as file_ptr:
            for line in new_lines:
                file_ptr.write("".join(line))
        os.system(f"autopep8 --in-place {out_orchestrator_path}")
        # os.system(f"autopep8 --in-place {out_orchestrator_path}")
                
# input_path='/home/tarun/Azure/ip_orchestrtor.py'
# output_path='/home/tarun/Azure/out_orch.py'
# async_update.orchestrator_async_update(input_path,output_path,{"WaitXSeconds"})


    