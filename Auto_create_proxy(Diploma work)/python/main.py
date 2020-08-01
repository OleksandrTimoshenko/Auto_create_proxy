from datetime import datetime  
import os,sys, time

location_dict = {
'East Asia':'eastasia',
'Southeast Asia':'southeastasia',
'Central US':'centralus',
'East US':'eastus',
'East US 2':'eastus2',
'West US':'westus',
'North Central US':'northcentralus',
'South Central US':'southcentralus',
'North Europe':'northeurope',
'West Europe':'westeurope',
'Japan West':'japanwest',
'Japan East':'japaneast',
'Brazil South': 'brazilsouth',
'Australia East': 'australiaeast',
'Australia Southeast': 'australiasoutheast',
'South India': 'southindia',
'Central India':'centralindia',
'West India': 'westindia',
'Canada Central':'canadacentral',
'Canada East':'canadaeast',
'UK South':'uksouth',
'UK West': 'ukwest',
'West Central US':'westcentralus',
'West US 2': 'westus2',
'Korea Central':'koreacentral',
'Korea South':'koreasouth',
'France Central':'francecentral',
'France South':'francesouth',
'Australia Central': 'australiacentral',
'Australia Central 2':'australiacentral2',
'South Africa North': 'southafricanorth',
'South Africa West':  'southafricawest'
}

path_to_ansible_hosts_file = '/home/alex/ansible/hosts.txt'                     # use it when add hosts to file
path_to_squid_conf_file = '/etc/squid/squid.conf'                               # use it to add new IP to ACL list
path_to_id_rsa_pub = '/home/alex/python/id_rsa.pub'                             # use to copy public key to new mashine when crate it 
path_to_yuml_file = '/home/alex/ansible/test_playbook.yml'                      # use to start configuring new mashine
path_to_new_cert = '/home/alex/squid-ca-cert.pem/1/home/alex/squid-ca-cert.pem' # use to return private cetrificate file to user
path_to_cert_folder =  '/home/alex/my_sert/'                                    # paths to file withs all certificates

### get machine ip from ip file
def parse_ip_file(file_location):
    f = open(file_location, 'r')
    for line in f.readlines():
        if line.find("publicIpAddress") != -1:
            ip = line[22:-3]
    f.close()
    return ip

### get text from file
def get_text_from_file(my_file):
    line_arr = []
    f =  open(my_file,"r")
    for line in f.readlines():
        line_arr.append(line[:-1])
    return line_arr

### ping mashine
def ping_check(ip):
    r = os.system("ping -c 4 " + ip)
    if r == 0:
        return True
    else:
        return False
    return True

### add machine ip to vm_list.txt
def add_ip_to_file(file,ip, user_location):
    f = open(file,'a')
    f.write(ip + ' ' + user_location + "\n")
    f.close()

### write client ip to squid.conf file if ip is not in file yet
def add_user_ip_to_squid_conf(user_ip):
    with open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "defoult.conf"), 'rt') as in_f:
        with open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "new.conf"), 'wt+') as out_f:
            out_f.seek(0)
            for line in in_f.readlines():
                if (line.find("acl user_mashine src") != -1)  and (line.find(user_ip) == -1):         
                    out_f.write(line.replace('\n','') + ' ' + user_ip + '\n')
                else:
                    out_f.write(line)
    os.system("rm " + os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "defoult.conf"))
    os.system('mv '+ os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "new.conf") + ' ' 
               + os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "defoult.conf"))

### add to Ancible comand flag that indicate needed machine
def chenge_playboock(location):
    with open('/home/alex/ansible/test_playbook.yml', 'rt') as in_f:
        with open('/home/alex/ansible/new_test_playbook.yml', 'wt+') as out_f:
            out_f.seek(0)
            for line in in_f.readlines():
                if line.find("- hosts:") != -1:
                    out_f.write('- hosts: squid_server_' + location + '\n')
                else:
                    out_f.write(line)
    os.system("rm /home/alex/ansible/test_playbook.yml")
    os.system('mv /home/alex/ansible/new_test_playbook.yml  \
               /home/alex/ansible/test_playbook.yml')

### add mashine IP to Ansible host file
def add_host_to_ansible(location, ip):
    with open(path_to_ansible_hosts_file, 'a+') as hosts:
        hosts.write('\n')
        hosts.write('[squid_server_' + location +']\n')
        hosts.write('1 ansible_host=' + ip +'\n')

### get certificate from file
def get_text_from_cert_file(location):
    return open((path_to_cert_folder + location + '.sert'),"r").read()

### add new certificate to certificate foldef
def add_new_cert_file(location):
    if os.path.exists(path_to_cert_folder + location + '.sert'):
        os.system('rm ' + path_to_cert_folder + location + '.sert')
    os.system('mv '+ path_to_new_cert + ' ' + path_to_cert_folder + location + '.sert') 

### check existing mashine
def check_and_create(machines_list,user_location,user_ip):        
    machine_exist = False
    if user_location in location_dict.keys():
        for mashine in machines_list:
            if (mashine[len(mashine)-len(user_location):] == user_location):     
                machine_exist = True
                add_user_ip_to_squid_conf(user_ip)
                location = location_dict[user_location]
                if not ping_check(mashine[:-(len(user_location)+1)]):            
                    print("Your VM is starting ...")
                    os.system('az vm start -g ' + location +'RG -n ' + location + 'VM')
                    time.sleep(100)
                print("Add user IP to squid ACL list")
                os.system('cd ~/ansible/ && ansible squid_server_' + location + \
                          ' -m file -a "path=' + path_to_squid_conf_file + ' state=absent" -b')                                                         
                # command to copy defoult.conf file to squide and restart
                os.system('cd ~/ansible/ && ansible squid_server_' + location + \
                          ' -m copy -a "src=' + os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "defoult.conf") 
                          + ' dest=' + path_to_squid_conf_file + ' mode=777" -b')                                           
                os.system('cd ~/ansible/ && ansible squid_server_' + location + \
                          ' -m command -a "systemctl restart squid" -b')  
                mashine_ip = mashine[:-(len(user_location)+1)]
                return mashine_ip
        if machine_exist == False:
            print("We dont have proxy server in this location yet...")
            mashine_ip = create_mashine(location_dict[user_location],user_location)        
            return mashine_ip
    else:
        raise RuntimeError('wrong location')

### check input parameters for correctness
def check_parametrs_numeric(arg):
    n = len(arg)
    if n == 2:    
        if ((arg[1] == '-h') or (arg[1] == '--help')):
            print("""
            This program is intended for deployment of proxy servers,
            in order to work properly, it needs to be given two parameters:
            1 - location for your proxy server (the list is the same as the list of locations for Azure virtual machines);
            2 - client IP address""")
            exit(0)
        else:
            print("Wrong number of arguments")
            print("use -h or --help to get help")
            exit(0)
    elif(n != 4  and n !=5 ):
        print("Wrong number of arguments")
        print("use -h or --help to get help")
        exit(0)

### get Azure CLI credentials from file Azure_cred.txt
def get_credential_from_file(file):
    with open(file, 'rt') as f:
        for line in f:
            if (line.find("name") != -1):
                name = line[11:-3]
            if (line.find("password") != -1):
                password = line[15:-3]
            if (line.find("tenant") != -1):
                tenant = line[13:-2]
    return name, password, tenant

### create new virtual mashine
def create_mashine(location, user_location):
    print('Your VM is creating, it may take a few minutes...')
    ### login to azure CLI with client-prinsipal
    cred_array = get_credential_from_file(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Azure_cred.txt"))
    os.system('az login --service-principal -u ' 
              + cred_array[0] + ' -p ' 
              + cred_array[1] + ' --tenant ' 
              + cred_array[2])
    ### create RG
    os.system('az group create -l ' + location + ' -n ' + location + 'RG')
    ### create cleare VM in new RG
    os.system('az vm create --resource-group ' 
              + location + 'RG --name ' 
              + location + 'VM   --image CentOS \
              --admin-username alex   --ssh-key-value '
               + path_to_id_rsa_pub + '  --output json \
              --verbose   --size Standard_A1_v2 > ' 
              + os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "ip"))
    ### Open mashine ports for squid
    os.system('az network nsg rule create --name test_role1 --nsg-name '
              + location + 'VMNSG   --resource-group ' 
              + location +'RG --access Allow --protocol icmp  \
              --direction Outbound --priority 100 \
              --source-port-range "*" --destination-port-range "*"')
    time.sleep(1)
    os.system('az network nsg rule create --name test_role2 --nsg-name '
              + location + 'VMNSG   --resource-group ' 
              + location +'RG --access Allow --protocol icmp \
              --direction Inbound --priority 100 \
              --source-port-range "*" --destination-port-range "*"')
    time.sleep(1)
    os.system('az network nsg rule create --name test_role3 --nsg-name '
              + location + 'VMNSG   --resource-group ' 
              + location +'RG --access Allow --protocol "*" \
              --direction Inbound --priority 200 \
              --source-port-range "*" --destination-port-range 3128 3129')
    time.sleep(1)
    os.system('az network nsg rule create --name test_role4 --nsg-name '
              + location + 'VMNSG   --resource-group ' 
              + location +'RG --access Allow --protocol "*" \
              --direction Outbound --priority 200 --source-port-range "*" \
              --destination-port-range 3128 3129')
    ip = parse_ip_file(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "ip"))
    add_ip_to_file(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "vm_list.txt"), ip, user_location)
    add_host_to_ansible(location, ip)
    add_user_ip_to_squid_conf(user_ip)
    chenge_playboock(location)                                          ### change main group in playbook
    print("Now we will install the proxy server and configure it...") 
    os.system('cd ~/ansible/ && ansible-playbook ./test_playbook.yml')  ### install squid and configure it using ansible playbook
    add_new_cert_file(location)
    return ip

if __name__ == "__main__":
    start_time = datetime.now()
    check_parametrs_numeric(sys.argv)
    if len(sys.argv) == 4:
        user_location = sys.argv[1] + ' ' + sys.argv[2]
        user_ip = sys.argv[3]
    else:
        user_location = sys.argv[1] + ' ' + sys.argv[2] + ' ' + sys.argv[3]
        user_ip = sys.argv[4]
    
    machines_list = get_text_from_file(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "vm_list.txt"))
    mashine_ip = check_and_create(machines_list, user_location,user_ip)
    print("IP of your proxy server is: " + mashine_ip)

    certificate = get_text_from_cert_file(location_dict[user_location])
    print('You can use this certificare to encrypt your http connections, if you can not use https')
    print(certificate)
    machines_list = get_text_from_file(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "vm_list.txt"))
    add_user_ip_to_squid_conf(user_ip)
    print("Code execution time: " + str(datetime.now() - start_time))