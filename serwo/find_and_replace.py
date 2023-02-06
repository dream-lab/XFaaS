import sys

def f_and_r(input_path, output_path, find_string, replace_string):
    f = open(input_path,'r')
    data_in = f.read()
    data_out = data_in.replace(find_string, replace_string )
    f2 = open(output_path,'w')
    f2.write(data_out)

if __name__ == '__main__':
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    find_string = sys.argv[3]
    replace_string = sys.argv[4]
    f_and_r(input_path,output_path,find_string,replace_string)
