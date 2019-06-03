'''
Created by PERSYN Loic
ON : 02-15-2019
LAST UPDATE : 02-22-2019
ROLE : Scan the VLAN. Write data in a csv file as well as in the database
'''

#Resources
import re
import subprocess
import sys
import mysql.connector as mariadb
from optparse import OptionParser
from mysql.connector import Error


########################
########################

#Functions

def get_segmented_ip(first_ip,last_ip):    
    #Split the first IP
    segmented_ip_start = re.search(r"(?P<first_part>[0-9]*).(?P<second_part>[0-9]*).(?P<third_part>[0-9]*).(?P<fourth_part>[0-9]{1,})",first_ip)
    #Check the first IP
    if segmented_ip_start is not None:
            get_segmented_ip.start_ip_first_part  = int(segmented_ip_start.group('first_part'))
            get_segmented_ip.start_ip_second_part = int(segmented_ip_start.group('second_part'))
            get_segmented_ip.start_ip_third_part  = int(segmented_ip_start.group('third_part'))
            get_segmented_ip.start_ip_fourth_part = int(segmented_ip_start.group('fourth_part'))
            if get_segmented_ip.start_ip_fourth_part == 0:
                get_segmented_ip.start_ip_fourth_part += 1
    else : 
            sys.exit("Error first IP! - ! Second input not checked !")
    
    #Split the last IP
    segmented_ip_finish = re.search(r"(?P<first_part>[0-9]*).(?P<second_part>[0-9]*).(?P<third_part>[0-9]*).(?P<fourth_part>[0-9]{1,})",last_ip)
    #Check the last IP
    if segmented_ip_finish is not None:
            get_segmented_ip.finish_ip_first_part  = int(segmented_ip_finish.group('first_part'))
            get_segmented_ip.finish_ip_second_part = int(segmented_ip_finish.group('second_part'))
            get_segmented_ip.finish_ip_third_part  = int(segmented_ip_finish.group('third_part')) 
            get_segmented_ip.finish_ip_fourth_part = int(segmented_ip_finish.group('fourth_part')) 
    else : 
            sys.exit("Error last IP!")
    return;  
   

#----------------------#


def analyse_ip(ip): 
   #Will analyse the IP with ping, nslookup and nmap
   #Populate the variable csv_var   
   #Feature 1 - Get the host name of the machine
   ping_resp = subprocess.Popen('ping -c 1 ' + ip ,stdout=subprocess.PIPE, shell=True)
   (output,err) = ping_resp.communicate()
   check_ping = re.search(r"From *\d*\D\d*\D\d*\D\d* \w*\D\d (?P<unreachable>\w*)",output)
   if check_ping is not None:
    return    
   else:
		try:
			nsl_resp = subprocess.Popen('nslookup ' + ip,stdout=subprocess.PIPE, shell=True)   
			(output,err) = nsl_resp.communicate()             
			full_line = re.search(r"(?P<host>(?<=name = ).*)", output)
			if full_line is not None:
				 full_host = full_line.group('host')
				 full_name = re.search(r"(?P<name>^(.*?)(?=\.))", full_host)
				 host_name = full_name.group('name')
				 #Feature 2 - Get the OS running on the machine
				 if 'bewx' in host_name or 'beqcaa' in host_name:
					 os = "WINDOWS"
				 elif 'bewxp' in host_name:
					 os = "WINDOWS in PAC"  
				 elif 'beap' in host_name:
					 os = "AIX"  
				 elif 'berp' in host_name or 'berx' in host_name:
					 os = "RHEL"
				 else :
					 os = "unknown"   
			else:
				 host_name = ""
				 os = "unknown"
			csv_var = ip + "," + host_name + "," + os + ","            
		except:
			sys.exit("--nslookup Error")
		try:
			#Feature 3 - Check if specific ports are opened
			nmap_result = subprocess.check_output('nmap -p 22,80,443,3389 ' + ip , shell=True)        
			full_status = re.search(r"(22\/tcp *(?P<ssh_status>[a-z]*).*ssh[\r\n]+80\/tcp *(?P<http_status>[a-z]*).*http[\r\n]+443\/tcp *(?P<https_status>[a-z]*).*https[\r\n]+3389\/tcp *(?P<rdp_status>[a-z]*))",nmap_result)             
			
			if full_status is not None:
				if full_status.group('ssh_status') == 'open':
				   ssh_status = 'ssh'
				else : ssh_status = ''
				if full_status.group('http_status') == 'open':
				   http_status  = 'http'
				else : http_status = ''
				if full_status.group('https_status') == 'open':
				   https_status = 'https'
				else : https_status = ''
				if full_status.group('rdp_status') == 'open':
				   rdp_status = 'rdp'
				else : rdp_status  = ''   
				csv_var += ssh_status + "," + http_status + "," + https_status + "," + rdp_status
			else:
				 csv_var += ",,,"  
			if host_name != "":
				 f.write(csv_var + "\n") 
		except:
			sys.exit("--nmap Error--")
   return;
      
########################
########################

#Create the man for the bash => python vlan_scan_v2.py -h/--help
parser = OptionParser()
parser.add_option("-f", "--firstIP", action="store", type="string", dest="first_ip", help="Write the first IP you want to start the scan with", metavar="XXX.XXX.XXX.XXX")
parser.add_option("-l", "--lastIP", action="store", type="string", dest="last_ip", help="Write the last IP you want to finish the scan with", metavar="XXX.XXX.XXX.XXX")
(options, args) = parser.parse_args()

#Check the input form client and ask for missing parameters if so
first_ip = options.first_ip
last_ip = options.last_ip
if first_ip is None:
  first_ip = raw_input("Please enter the ip you want to START the scan with (XXX.XXX.XXX.XXX) : ")
if last_ip is None:
  last_ip = raw_input("Please enter the ip you want to FINISH the scan with (XXX.XXX.XXX.XXX) : ")
  
#Call the function to split the IPs
get_segmented_ip(first_ip,last_ip)


#Variables
file_name = 'csv_import.csv'
csv_var = ""
third_part_ip_start = get_segmented_ip.start_ip_third_part
third_part_ip_finish = get_segmented_ip.finish_ip_third_part
fourth_part_ip_start = get_segmented_ip.start_ip_fourth_part
fourth_part_ip_finish = get_segmented_ip.finish_ip_fourth_part
max_value_ip = 255 #Max value for an ip

########################
########################

#Open the CSV file + write the header
f = open(file_name, "w+")
f.write("IP,hostname,OS,SSH,HTTP,HTTPS,RDP\n")

try:
	while third_part_ip_start <= third_part_ip_finish:
		if third_part_ip_start == third_part_ip_finish:
			while fourth_part_ip_start <= fourth_part_ip_finish:
				current_ip = str(get_segmented_ip.start_ip_first_part) + "." + str(get_segmented_ip.start_ip_second_part) + "." + str(third_part_ip_start) + "." + str(fourth_part_ip_start)
				print current_ip
				try:
					analyse_ip(current_ip)
					fourth_part_ip_start += 1
				except:
					sys.exit("--Analyse Error--")
		else:
			while fourth_part_ip_start < max_value_ip:
				current_ip = str(get_segmented_ip.start_ip_first_part) + "." + str(get_segmented_ip.start_ip_second_part) + "." + str(third_part_ip_start) + "." + str(fourth_part_ip_start)
				print current_ip
				try:
					analyse_ip(current_ip)
					fourth_part_ip_start += 1
				except:
					sys.exit("--Analyse Error--")
			if fourth_part_ip_start == max_value_ip:
				fourth_part_ip_start = 1
			else: break
		connection = mariadb.connect(host='192.168.6.65', user='root', password='', database='db_test')
		if connection.is_connected():
			ip_db = current_ip
			hostname_db = host_name
			os_db = os
			ssh_port_db = ssh_port
			http_port_db = http_port
			https_port_db = https_port
			rdp_port_Db = rdp
			cursor = connection.cursor()
			cursor.execute("INSERT INTO test (ip,hostname,os,ssh_port,http_port,https_port,rdp_port) VALUES (%s,%s,%s,%s,%s,%s,%s);", (ip_db,hostname_db,os_db,ssh_port_db,http_port_db,https_port_db,rdp_port_db))
			connection.commit() 
		third_part_ip_start += 1  
except Error as e:
	print("Error while connecting to MySQL", e)
finally:
	try:
		if(connection.is_connected()):
			#Close the cursor and the connection of MySQL
			cursor.close()
			connection.close()
			print("MySQL connection is closed")		
	except:
		print("--No Connection Established--")
#Close the CSV file
f.close()
   
########################
########################

