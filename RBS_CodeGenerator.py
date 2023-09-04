import json
import numpy as np

task_set = []

class RBS_task:
    def __init__(self, id, A, C, T, D, S, number_of_nodes, number_of_sequences):
        self.id = id
        self.priority = 0
        self.adj = A
        self.ex_times = C
        self.period = T
        self.deadline = D
        self.sequences = S
        self.number_of_nodes = number_of_nodes
        self.number_of_sequences = number_of_sequences

def list_to_integer(list):
    #list.reverse()
    value = 0
    for index in range(len(list)):
        if list[index] == 0:
            continue
        else:
            value = value + pow(2, index)
    return(value)

def compute_adj_matrix(A, number_of_nodes):

    #define matrix size
    adj_matrix = [[0 for i in range(number_of_nodes)] for i in range(number_of_nodes)]

    for element in A:
        row_ind = element[1] - 1
        col_ind = element[0] - 1
        adj_matrix [row_ind][col_ind] = 1    

    return adj_matrix

def import_taskset():
    f = open('taskset2.json', "r")
    data = json.load(f)
    
    #Parse tasks from JSON file
    for task in data['taskset']:
        id = task['id']
        E = list(task['E'])
        C = list(task['C'])
        T = int(task['T'])
        D = int(task['T'])
        S = list(task['SEQ'])
        CPU = list(task['AFF'])

        #Compute the number of nodes
        number_of_nodes = 0
        for element in E:
            for index in range(2):
                if element[index] > number_of_nodes:
                    number_of_nodes = element[index]

        #Compute the number of sequences
        number_of_sequences = len(S)
        
        #Add task to taskset list
        imported_task = RBS_task(id, compute_adj_matrix(E, number_of_nodes), C, T, D, S, number_of_nodes, number_of_sequences)
        task_set.append(imported_task)

    f.close()

def generate_seq_c_file():
    sequencesC = open("sequences.c","w")
    sequencesC.write("#include \"sequences.h\"\n")


    #generate array with sequence functions pointers
    sequencesC.write("\n")
    sequencesC.write("//sequence functions pointers\n")
    for task in task_set:
        string = "void *(*seq_func_ptr_t"+ str(task.id) + "[" + str(task.number_of_sequences) + "])() = {"
        sequencesC.write(string)
        for element in task.sequences:
            if task.sequences.index(element) == 0:
                string = "sequence_" + str(task.id) + "_" + str((task.sequences.index(element)+1)) + "_function"
                sequencesC.write(string)
            else:
                string = ", sequence_" + str(task.id) + "_" + str((task.sequences.index(element)+1)) + "_function"
                sequencesC.write(string)
        sequencesC.write("};\n")

    #generate array with node functions pointers
    sequencesC.write("\n")
    sequencesC.write("//node functions pointers\n")
    for task in task_set:
        string = "void *(*nodes_func_ptr_t"+ str(task.id) + "[" + str(task.number_of_nodes) + "])() = {"
        sequencesC.write(string)
        for i in range(1, (task.number_of_nodes + 1)):
            if i == 1:
                string = "node_" + str(task.id) + "_" + str(i)
                sequencesC.write(string)
            else:
                string = ", node_" + str(task.id) + "_" + str(i)
                sequencesC.write(string)
        sequencesC.write("};\n")

    #generate arrays with precedence constraints
    sequencesC.write("\n")
    sequencesC.write("//precedence constraints\n")    
    for task in task_set:

        string = "u_int32_t T" + str(task.id) + "_precedence_constraints_h[" + str(task.number_of_nodes) + str("] = {")
        sequencesC.write(string)
        for i in range(0, task.number_of_nodes):
            value = list_to_integer(task.adj[i])
            if i == 0:
                string = str(value)
                sequencesC.write(string)
            else:
                string = ", " + str(value)
                sequencesC.write(string)

        sequencesC.write("};\n")

        string = "u_int32_t T" + str(task.id) + "_precedence_constraints_v[" + str(task.number_of_nodes) + str("] = {")
        sequencesC.write(string)
        for i in range(0, task.number_of_nodes):
            vertical_list = []
            for k in range(len(task.adj)):
                vertical_list.append(task.adj[k][i])
            value = list_to_integer(vertical_list)
            if i == 0:
                string = str(value)
                sequencesC.write(string)
            else:
                string = ", " + str(value)
                sequencesC.write(string)

        sequencesC.write("};\n")

    #generate array with sequence heads
    sequencesC.write("\n")
    sequencesC.write("//sequences heads\n")
    for task in task_set:

        #make a list and set all fields to 0
        nodes_list = [0 for i in range(task.number_of_nodes)]

        string = "u_int32_t T" + str(task.id) + "_sequence_heads[" + str(task.number_of_sequences) + "] = {"
        sequencesC.write(string)
        for element in task.sequences:
            index = element[0] - 1
            nodes_list[index] = task.sequences.index(element) + 1

        for k in range(task.number_of_nodes):
            if k == 0:
                string =  str(nodes_list[k])
                sequencesC.write(string)
            else:
                string = ", " + str(nodes_list[k])
                sequencesC.write(string)

        sequencesC.write("};\n")

    #generate task data structures
    sequencesC.write("\n")
    sequencesC.write("//task data structures\n")
    for task in task_set:  

        string = "struct task_data task" + str(task.id) + "_data = { "
        sequencesC.write(string)

        string = ".task_id =" + str(task.id)
        sequencesC.write(string)

        string = ", .priority =" + str(task.priority)
        sequencesC.write(string)

        string = ", .number_of_nodes =" + str(task.number_of_nodes)
        sequencesC.write(string)

        string = ", .number_of_sequences = " + str(task.number_of_sequences)
        sequencesC.write(string)

        string = ", \n.job_counter = 0"
        sequencesC.write(string)       

        string = ", .pre_cons_h = T" + str(task.id) + "_precedence_constraints_h"
        sequencesC.write(string)

        string = ", .pre_cons_v = T" + str(task.id) + "_precedence_constraints_v"
        sequencesC.write(string)

        string = ", \n.sequence_heads = T" + str(task.id) + "_sequence_heads"
        sequencesC.write(string)

        string = ", .sequences_guards = semaphores_T" + str(task.id)
        sequencesC.write(string)

        string = ", .last_added_job = NULL"
        sequencesC.write(string) 

        string = ", \n.func = {"
        sequencesC.write(string)

        for x in range(1,task.number_of_nodes+1):

            if x == 0:
                string = "node_" + str(task.id) + "_" + str(x)
                sequencesC.write(string)

            else:
                string = ", node_" + str(task.id) + "_" + str(x)
                sequencesC.write(string)

        sequencesC.write("}}; \n")

    #generate sequences functions
    sequencesC.write("\n")
    sequencesC.write("//sequences functions\n")
    for task in task_set:
        for element in task.sequences:

            string = "void *sequence_" + str(task.id) + "_" + str((task.sequences.index(element) + 1)) + "_function(void *arguments)\n{\n"
            sequencesC.write(string)

            string = "set_cpu(" + str((task.sequences.index(element))) + ")\n"
            sequencesC.write(string)

            sequencesC.write(" struct sequence_data *seq_data = (struct sequence_data*) arguments;\n")

            sequencesC.write(" while(true)\n  {\n")

            sequencesC.write("   WaitNextJob(seq_data);\n")

            for item in element:
                sequencesC.write("\n")
                string = "   if(TryExecuteNode(seq_data," +  str(item) + ") != 0)\n   {\n" + "     TerminateSequence(seq_data, " + str(item) + ");\n"
                sequencesC.write(string)
                sequencesC.write("     continue;\n   }\n")

            sequencesC.write("\n")
            sequencesC.write("   FinishJob(seq_data);\n")
            sequencesC.write("  }\n}\n")

    sequencesC.close()

def generate_seq_h_file():
    sequencesH = open("sequences.h","w")

    #generate includes and defines
    sequencesH.write("#ifndef SEQUENCES_H\n")
    sequencesH.write("#define SEQUENCES_H\n")
    sequencesH.write("#include \"rbs_lib.h\"\n")
    sequencesH.write("#include \"workload.h\"\n")

    #generate task data structures
    sequencesH.write("\n")
    sequencesH.write("//tasks data structures\n")
    for task in task_set:
        string = "struct task_data task" + str(task.id) + "_data;\n"
        sequencesH.write(string)

    #generate array with sequence functions pointers
    sequencesH.write("\n")
    sequencesH.write("//sequence functions pointers\n")
    for task in task_set:
        string = "void *(*seq_func_ptr_t" + str(task.id) + "["+ str(task.number_of_sequences) + "])();\n"
        sequencesH.write(string)

    #generate array with node functions pointers
    sequencesH.write("\n")
    sequencesH.write("//node functions pointers\n")
    for task in task_set:
        string = "void *(*nodes_func_ptr_t" + str(task.id) + "["+ str(task.number_of_nodes) + "])();\n"
        sequencesH.write(string)

    #generate arrays with v and h precedence constraints
    sequencesH.write("\n")
    sequencesH.write("//horizontal and vertical precedence constraints\n")
    for task in task_set:
        string = "u_int32_t T" + str(task.id) + "_precedence_constraints_h["+ str(task.number_of_nodes) + "];\n"
        sequencesH.write(string)
        string = "u_int32_t T" + str(task.id) + "_precedence_constraints_v["+ str(task.number_of_nodes) + "];\n"
        sequencesH.write(string)

    #generate sequence heads structures
    sequencesH.write("\n")
    sequencesH.write("//arrays with sequence heads\n")
    for task in task_set:
        string = "u_int32_t T" + str(task.id) + "_sequence_heads["+ str(task.number_of_nodes) + "];\n"
        sequencesH.write(string)

    #generate array with semaphores
    sequencesH.write("\n")
    sequencesH.write("//semaphores\n")
    for task in task_set:
        string = "sem_t semaphores_T" + str(task.id) + "["+ str(task.number_of_sequences) + "];\n"
        sequencesH.write(string)

    #generate array with threads
    sequencesH.write("\n")
    sequencesH.write("//threads\n")
    for task in task_set:
        string = "pthread_t task" + str(task.id) + "_threads["+ str(task.number_of_sequences) + "];\n"
        sequencesH.write(string)


    #generate sequence functions
    sequencesH.write("\n")
    sequencesH.write("//sequence functions prototypes\n")    
    for task in task_set:
        for i in range(1, task.number_of_sequences + 1):
            string = "void *sequence_" + str(task.id) + "_"+ str(i) + "_function(void *arguments);\n"
            sequencesH.write(string)
        
    sequencesH.close()

def generate_workload_c_file():
    workloadC = open("workload.c","w")
    workloadC.write("#include \"workload.h\"\n")

    #workloadC.write("volatile u_int32_t mask[11] = {1,2,3,4,5,10,5,4,3,2,1};\n")

    #generate workload creator function
    #workloadC.write("void create_workload()\n{\n")
    #workloadC.write(" for(int p = 0; p <10001; p++)\n {\n")
    #workloadC.write("  conv_array[p] = p+9;\n")
    #workloadC.write(" }\n}\n")

    #one time unit function
    #workloadC.write("one_time_unit_workload()\n{\n")

    # workloadC.write("  int temp_value = 0;\n")
    # workloadC.write("\n struct timespec tim;\n")
    # workloadC.write("\n clock_gettime(CLOCK_REALTIME, &tim);\n")

    # workloadC.write("\n int rest = tim.tv_nsec % 9;\n")
    # workloadC.write("\n int start_index = rest*1000;\n")

    # workloadC.write("\n for(int big_index = start_index; big_index < start_index + 100; big_index++)\n {\n")

    # workloadC.write("  for(int small_ind = -5; small_ind <6; small_ind++)\n  {\n")

    # workloadC.write("    int index = big_index + small_ind;\n")
    # workloadC.write("    if(index < 0 || index > 9999)\n    {\n     ;\n    }\n")
    # workloadC.write("    else\n    {\n     temp_value = temp_value + conv_array[index] * mask[(small_ind + 5)];\n    }\n")

    # workloadC.write("\n  }\n")
    # workloadC.write("\n }\n")

    # workloadC.write(" temp_value = temp_value / 100;\n")
    # workloadC.write(" conv_array[start_index + 50] = temp_value;\n")
    # workloadC.write("}\n")

    #generate node functions
    workloadC.write("\n")
    workloadC.write("//node functions prototypes\n")
    for task in task_set:
        for node in range(1, task.number_of_nodes + 1):
            string = "void node_" + str(task.id) + "_"+ str(node) + "()\n{\n"
            workloadC.write(string)
            string = " for(int time_unit = 0; time_unit < " + str(task.ex_times[node-1]) + "; time_unit ++)\n  {\n"
            workloadC.write(string)

            workloadC.write("   one_time_unit_workload();\n")

            workloadC.write("  }\n")
            workloadC.write("}\n")




def generate_workload_h_file():
    workloadH = open("workload.h","w")

    #generate includes and defines
    workloadH.write("#ifndef WORKLOAD_H\n")
    workloadH.write("#define WORKLOAD_H\n")
    workloadH.write("#define _GNU_SOURCE\n")
    workloadH.write("#include <stdio.h>\n")
    workloadH.write("#include <stdlib.h>\n\n")
    workloadH.write("#include <otw.h>\n\n")

    #workloadH.write("volatile u_int32_t conv_array[10000];\n")
    #workloadH.write("volatile u_int32_t mask[11];\n")

    #workloadH.write("\n//create workload\n")
    #workloadH.write("void create_workload();\n")

    #workloadH.write("\n//one time unit workload\n")
   # workloadH.write("void one_time_unit_workload();\n\n")

    #generate nodes functions
    workloadH.write("\n")
    workloadH.write("//nodes functions prototypes\n")    
    for task in task_set:
        for node in range(1, task.number_of_nodes + 1):
            string = "void node_" + str(task.id) + "_"+ str(node) + "();\n"
            workloadH.write(string)


def generate_otw_c_file():
    otwC = open("otw.c","w")
    otwC.write("volatile int conv_array[10100] = {\n")
    x = np.random.randint(100)
    string =  str(x) 
    otwC.write(string)
    string = ", " + str(x)
    for i in range(10099):
        if ((i % 25) == 0):
            x = np.random.randint(1000)
            string = ", " + str(x) + "\n"
            otwC.write(string)
        else:
            x = np.random.randint(100)
            string = ", " + str(x)
            otwC.write(string)
    otwC.write("};\n")

def main():
    import_taskset()
    generate_seq_h_file()
    generate_seq_c_file()
    generate_workload_h_file()
    generate_workload_c_file()
    generate_otw_c_file()



if __name__ == "__main__":
    main()
