
import json
import numpy as np

task_set = []

class RBS_task:
    def __init__(self, id, P, CPU, A, C, T, D, S, number_of_nodes, number_of_sequences):
        self.id = id
        self.priority = P
        self.adj = A
        self.ex_times = C
        self.period = T
        self.deadline = D
        self.sequences = S
        self.cpu = CPU
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
        P = task['P']
        CPU = list(task['AFF'])

        P = 99 - P

        #Compute the number of nodes
        number_of_nodes = 0
        for element in E:
            for index in range(2):
                if element[index] > number_of_nodes:
                    number_of_nodes = element[index]

        #Compute the number of sequences
        number_of_sequences = len(S)
        
        #Add task to taskset list
        imported_task = RBS_task(id, P, CPU, E, C, T, D, S, number_of_nodes, number_of_sequences)
        task_set.append(imported_task)

    f.close()

def global_c_file():
    globalC = open("global.c","w")
    globalC.write("#include \"global.h\"\n")

    string = "int prio[" + str(len(task_set)) + "] = {"
    globalC.write(string)
    for task in range(0, len(task_set)):
        if task == len(task_set) - 1:
            string = str(task_set[task].priority) + "};\n"
            globalC.write(string)
        else:
            string = str(task_set[task].priority) + ","
            globalC.write(string)

    string = "int periods[" + str(len(task_set)) + "] = {"
    globalC.write(string)
    for task in range(0, len(task_set)):
        if task == len(task_set) - 1:
            string = str(task_set[task].period) + "};\n"
            globalC.write(string)
        else:
            string = str(task_set[task].period) + ","
            globalC.write(string)



    #generate sequences functions
    globalC.write("\n")
    globalC.write("//sequences functions\n")
    for task in task_set:
        for node in range(1, (task.number_of_nodes +1)):

            string = "void *node_" + str(task.id) + "_" + str(node) + "_function(void *arguments)\n{\n"
            globalC.write(string)

            globalC.write("int job = 0;\n")
            string = "  int task = " + str(task.id) + ";\n"
            globalC.write(string)
            string = "  int node = " + str(node) + ";\n"
            globalC.write(string)


            string = "while(1)\n{\n"
            globalC.write(string)

            string = "    job ++;\n"
            globalC.write(string)


            #If source node wait on release
            if node == 1:
                string = "    sem_wait(&semaphore_release[" + str(task.id-1) + "]);\n\n"
                globalC.write(string)

            #Wait on predecessors
            for element in task.adj:
                if element[1] == node:
                    string = "    sem_wait(&semaphore_" + str(task.id) + "_" + str(element[0]) + "_" + str(node) + ");\n"
                    globalC.write(string)

            #LOG
            globalC.write("    int index = int log_event_start(task, node, job, 1)")

            globalC.write("\n")
            string = "    for(int time_unit = 0; time_unit < " + str(task.ex_times[node-1]) + "; time_unit ++)\n    {\n"
            globalC.write(string)
            globalC.write("      one_time_unit_workload();\n")
            globalC.write("    }\n")

            #LOG
            globalC.write("    log_event_end(index)")

            #Inform successors
            globalC.write("\n")
            for element in task.adj:
                if element[0] == node:
                    string = "  sem_post(&semaphore_" + str(task.id) + "_" + str(node) + "_" + str(element[1]) + ");\n"
                    globalC.write(string)
            globalC.write("}\n")
            globalC.write("}\n")

    #init function
    string = "void initialize_tasks()\n{\n"
    globalC.write(string)

    for task in task_set:
        string = "  sem_init(&semaphore_release[" + str(task.id-1) + "], 0);\n\n"
        globalC.write(string)
        for element in task.adj:
            string = "  sem_init(&semaphore_" + str(task.id) + "_" + str(element[0]) + "_" + str(element[1]) + ", 0);\n"
            globalC.write(string)


    globalC.write("}\n")



    globalC.close()

def global_h_file():
    globalH = open("global.h","w")

    globalH.write("#ifndef GLOBAL_H\n")
    globalH.write("#define GLOBAL_H\n")
    globalH.write("#define _GNU_SOURCE\n")
    globalH.write("#include <stdio.h>\n")
    globalH.write("#include <semaphore.h>\n")
    globalH.write("#include <pthread.h>\n")
    globalH.write("#include <time.h>\n")
    globalH.write("#include <string.h>\n")
    globalH.write("#include <unistd.h>\n")
    globalH.write("#include <stdlib.h>\n\n")
    globalH.write("#include \"otw.h\"\n\n")
    globalH.write("#include \"log.h\"\n\n\n")

    string = "#define number_of_tasks " + str(len(task_set)) + "\n\n"
    globalH.write(string)

    string = "int periods[" + str(len(task_set)) + "];\n"
    globalH.write(string)

    string = "int prio[" + str(len(task_set)) + "];\n"
    globalH.write(string)

    string = "sem_t semaphore_release["+ str(len(task_set)) + "];\n"
    globalH.write(string)


    for task in task_set:
        for element in task.adj:
            string = "sem_t semaphore" + str(task.id) + "_" + str(element[0]) + "_" + str(element[1]) + ";\n"
            globalH.write(string)

    for task in task_set:
        for node in range(1, (task.number_of_nodes +1)):
            string = "pthread_t task" + str(task.id) + "_node_" + str(node) + ";\n"
            globalH.write(string)

    globalH.write("void initialize_tasks();\n")
    for task in task_set:
        for node in range(1, (task.number_of_nodes +1)):
            string = "void *node_" + str(task.id) + "_" + str(node) + "_function(void *arguments);\n"
            globalH.write(string)

    globalH.write("#endif\n")

def main_file():
    main = open("main.c","w")

    main.write("#define _GNU_SOURCE\n")
    main.write("#include <stdio.h>\n")
    main.write("#include <semaphore.h>\n")
    main.write("#include <pthread.h>\n")
    main.write("#include <time.h>\n")
    main.write("#include <string.h>\n")
    main.write("#include <unistd.h>\n")
    main.write("#include <stdlib.h>\n\n")
    main.write("#include \"log.h\"\n\n\n")

    main.write("int main()\n{\n")
    main.write("initialize_tasks();\n")
    main.write("int result = 0;\n")
    main.write("pthread_t job_release_threads[20];\n")

    main.write("pthread_attr_t attr[20];\n")
    main.write("struct sched_param schedPARAM[20];\n")




    for task in task_set:
        main.write("\n\n")
        main.write("\n\n")
        string = "pthread_attr_init(&attr[" + str(task.id) + "]);\n"
        main.write(string)
        string = "pthread_attr_setschedpolicy(&attr[" + str(task.id) + "],SCHED_FIFO );\n"
        main.write(string)
        string = "schedPARAM[" + str(task.id) + "].sched_priority = " + str(task.priority) + ";\n"
        main.write(string)
        string = "pthread_attr_setschedparam(&attr[" + str(task.id) + "], &schedPARAM[" + str(task.id) + "]);\n"
        main.write(string)
        string = "pthread_attr_setinheritsched(&attr[" + str(task.id) + "], PTHREAD_EXPLICIT_SCHED);\n"
        main.write(string)

        main.write("\n\n")
        for node in range(1, task.number_of_nodes +1):
            thread_string = "&task" + str(task.id) + "_node_" + str(node)
            func_string = "&node_" + str(task.id) + "_" + str(node) + "function"
            attr_string = "&attr[" + str(task.id) + "]"
            string = "result = pthread_create(" + thread_string + ", " + attr_string+ ", "+ func_string + ", NULL);\n"
            main.write(string)


    #Release mechanism
    main.write("\n\n")
    for task in task_set:
        main.write("struct job_timer_data *job_rel_tim" + str(task.id) + " = malloc(sizeof(struct job_timer_data));\n")
        string = "job_rel_tim" + str(task.id) + "->task_number = " + str(task.id) + ";\n"
        main.write(string)
        string = "job_rel_tim" + str(task.id) + "->period_in_usec = " + str(task.period) + ";\n"
        main.write(string) 
        string = "job_rel_tim" + str(task.id) +"->max_number_of_jobs = 100;\n"
        main.write(string)      

        string = "pthread_create(&job_release_threads[" + str(task.id) + "], NULL, &job_release_func, (void*) job_rel_tim" + str(task.id) +")\n"
        main.write(string)

    main.write("\n\n")
    for task in task_set:
        string = "pthread_join(job_release_threads[" + str(task.id) + "], NULL);\n"
        main.write(string)

    
    
    main.write("}\n")


def main():
    import_taskset()
    global_c_file()
    global_h_file()
    main_file()
    



if __name__ == "__main__":
    main()