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
    first_argument = '"' + str(first_argument) + '"'
    return str(variable_name), first_argument, str(second_argument)


def codegen_async_loop(in_var, out_var, func_name):
    """
    Generate a polling loop for the async function itself.
    
    This wraps the async function call in a while loop that:
    1. Calls the async function
    2. Checks if body["Poll"] is False
    3. If False, exits the loop
    4. If True, waits and retries
    
    Args:
        in_var: The input variable to the async function
        out_var: The output variable from the async function
        func_name: The name of the async function (e.g., "PollerNode")
    """
    # Use 4 spaces for indentation (Python standard)
    indent = "    "
    new_code = '\n'
    new_code += '\n' + indent + out_var + ' = ' + in_var
    new_code += '\n' + indent + 'while True:'
    new_code += '\n' + indent * 2 + out_var + ' = yield context.call_activity(' + func_name + ', ' + out_var + ')'
    new_code += '\n' + indent * 2 + 'body = unmarshall(json.loads(' + out_var + ')).get_body()'
    new_code += '\n' + indent * 2 + 'if not body.get("Poll", True) or body.get("Poll") == False:'
    new_code += '\n' + indent * 3 + 'break'
    new_code += '\n' + indent * 2 + 'else:'
    new_code += '\n' + indent * 3 + 'deadline = context.current_utc_datetime + timedelta(seconds=100)'
    new_code += '\n' + indent * 3 + 'yield context.create_timer(deadline)'
    new_code += '\n'
    return new_code


class async_update:
    def orchestrator_async_update(in_orchestrator_path, out_orchestrator_path, async_func_set):
        """
        Update the orchestrator to wrap async functions in polling loops.
        
        This modifies the orchestrator so that async functions are called in
        a loop until they return Poll: False.
        
        Logic (matching AWS behavior):
        1. Find lines that call async functions
        2. Replace those lines with a polling loop
        3. The loop checks the async function's output for Poll
        4. Successor functions are called AFTER the loop exits
        """
        print("Async Fn list", async_func_set)
        
        with open(in_orchestrator_path, 'r') as file_ptr:
            lines = file_ptr.readlines()

        new_lines = []
        for line in lines:
            if 'context.call_activity' in line:
                out_var, func_name, in_var = extract_var(line)
                # Remove quotes from func_name to compare
                func_name_clean = func_name[1:-1] if func_name.startswith('"') else func_name
                
                # Check if THIS function is the async function
                if func_name_clean in async_func_set:
                    # Wrap the async function call in a polling loop
                    new_code = codegen_async_loop(in_var, out_var, func_name)
                    print(new_code)
                    new_lines.append(new_code)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(out_orchestrator_path, 'w') as file_ptr:
            for line in new_lines:
                file_ptr.write("".join(line))
        
        os.system(f"autopep8 --in-place {out_orchestrator_path}")


# Example usage:
# input_path='/home/tarun/Azure/ip_orchestrtor.py'
# output_path='/home/tarun/Azure/out_orch.py'
# async_update.orchestrator_async_update(input_path,output_path,{"WaitXSeconds"})