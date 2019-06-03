import subprocess
import re
import sys
import argparse
import smtplib
import socket
from datetime import datetime

#Create the man for the bash => python siapi.py -h/--help
parser = argparse.ArgumentParser()
parser.add_argument("-i", action="store", type=str, help="Host IP", dest="address")
parser.add_argument("-n", action="store", type=str, help="Hostname", dest="name")
parser.add_argument("-z", action="store", type=str, help="Zone", dest="zone")
parser.add_argument("-a", nargs='+', help="Application(s)", dest="application")
parser.add_argument("-s", action="store", type=str, help="Operating System", dest="os")
parser.add_argument("-v", action="store", type=str, help="Version", dest="version")
parser.add_argument("-t", action="store", type=str, help="Instance", dest="instance")
parser.add_argument("-d", action="store", type=str, help="Database name", dest="db")
parser.add_argument("-u", action="store", type=str, help="Username", dest="user")

args = parser.parse_args()

#Variables
address = args.address
name = args.name
zone = args.zone
applications = args.application
os = args.os
version = args.version
instance = args.instance
db = args.db
username = args.user

error_msg = "Failed to load icinga_host"
idoit_api_key = "8z7x9i7jz8wsg4g8"
maillog= ""

class SilApi:

    new_t_list = ""
    existing_templates = ""
    formatted = ""
    
      
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    def push_to_icinga(self,ip,hostname,os,applications=[]):

      f = open("icinga_log.txt","a+")
      
      hosts = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X GET 'http://192.168.6.65/icingaweb2/director/hosts'", shell=True)
      check_result = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X GET 'http://192.168.6.65/icingaweb2/director/host?name=" + hostname + "'", shell=True)
      toutou = ""
      
      if ip in hosts:
        '''
        Host already exist in icinga
        Only existing templates will be added
        '''
        list_imports = re.search(r"\"imports\": \[[\n\r](?P<imports>[^]]+)",check_result)
        try:
          templates = list_imports.group('imports')
          temp_split = templates.split()
          temp_exist = ""
          for i in temp_split:
            temp_exist += i
            
          full_temp = temp_exist
          self.icinga_get_full_templates(os,f,applications)
          for i in applications:       
            if i in templates:
              self.get_date_formatted()
              f.write(formatted + " - ICINGA - SUCCESS - Template " + i + " already exists on host " + ip + "\n")
            else:
              toutou = full_temp + "," + new_t_list         
          if toutou != "":
            new_imports = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X POST 'http://192.168.6.65/icingaweb2/director/host?name=" + hostname +"' -d '{\"imports\": [" + toutou + "]}'", shell=True)
            self.deploy_icinga(f)
        
        except AttributeError:
          self.get_date_formatted()
          f.write(formatted + " ICINGA - ERROR   - IP " + ip + " already exists\n")
        except:
          self.get_date_formatted()
          f.write(formatted + " - ICINGA - ERROR   - Something went wrong")
          
      elif hostname in hosts:
        self.get_date_formatted()
        f.write(formatted + " - ICINGA - ERROR   - Trying to recreate host '" + hostname + "'\n")
      
      else: 
        '''
        Host does not exist in icinga
        He will be created
        Only existing templates will be added
        '''      
        self.icinga_get_full_templates(os,f,applications)
        if new_t_list != "":  
          create_host_cmd = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X POST 'http://192.168.6.65/icingaweb2/director/host' -d '{\"object_name\": \"" + hostname + "\",\"object_type\": \"object\",\"imports\": [" + new_t_list + "],\"address\": \"" + ip + "\"}'", shell=True)
          if "Traceback" in create_host_cmd:
            self.get_date_formatted()
            f.write(formatted + " - ICINGA - ERROR   - Host " + hostname + " with IP " + ip + " not created\n")
          else:
            self.deploy_icinga(f)
        else:
          self.get_date_formatted()
          f.write(formatted + " - ICINGA - ERROR   - An existing template is mandatory.\n")

 
      f.close()
 
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    def deploy_icinga(self,f):
      deploy = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X POST 'http://192.168.6.65/icingaweb2/director/config/deploy'", shell=True)
      if "checksum" in deploy:
        self.get_date_formatted()
        f.write(formatted + " - ICINGA - SUCCESS - Deployed\n")
      else:
        self.get_date_formatted()
        f.write(formatted + " - ICINGA - ERROR   - Deploy")

    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    def icinga_get_full_templates(self,os,f,apps=[]):
      global new_t_list
      new_t_list = ""
      existing_templates = subprocess.check_output("curl -k -s -H 'Accept: application/json' -u 'admin:admin' -X GET 'http://192.168.6.65/icingaweb2/director/hosts/templates'", shell=True) 
      counter = 0
      for i in apps:
        if i in existing_templates:
          if counter == 0 :
            new_t_list += "\"" + i + "\""
            counter += 1
          else:
            new_t_list += ",\"" + i + "\""
        else:
          #Creation of templates is not supported via the API
          self.get_date_formatted()
          f.write(formatted + " - ICINGA - ERROR   - Template " + i + " does not exist and will not be added\n")
                  
      if os in existing_templates:
        if counter == 0 :
          new_t_list += "\"" + os + "\""
          counter += 1
        else:
          new_t_list += ",\"" + os + "\""
      else:
        #Creation of templates is not supported via the API
        self.get_date_formatted()
        f.write(formatted + " - ICINGA - ERROR   - Template " + os + " does not exist and will not be added\n")
    
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    def send_mail(self):
      sender = 'loic.persyn@swift.com'
      receivers = ['loic.persyn@swift.com']
      maillog = "" 
      
      with open("/pac_share/Test_Data/AMH/Automation/AMH_Util/AMHDBVersionLister/maillog.txt") as f:
        for line in f.readlines():
          maillog += line
      
      message = """From: From SWIFT IT Asset Management <sitam@swift.com>
To: To Loic PERSYN <loic.persyn@swift.com>
Subject: Log file IT Asset Management      

Dear,
Please find below the line(s) where action from your side is required

""" + """""" + maillog + """\n\n\n""" 
      
      try:
        import os
        os.remove("/pac_share/Test_Data/AMH/Automation/AMH_Util/AMHDBVersionLister/maillog.txt")
        smtpObj = smtplib.SMTP('192.168.7.103')
        smtpObj.sendmail(sender, receivers, message) 
      
      except :
         print("")
    #-----------------------------------------------------------------------------------------------------------------------------------------#
  
    def amh_automation_update(self,database,username,version,owner,zone):
      global maillog
      
      f = open("idoit.log","a+")
      m = open("maillog.txt","a+")
      
      #Parse inputs
      re_db = re.search(r"\d\d\d.\d\d\d.\d.\d*:\d*\/(?P<db>.*)",database)
      re_user = re.search(r"\w{4}_\w{4}_(?P<hostname>\w{4,5}\d{2,5})_(?P<instance>.*)",username)
      
      #Set variables
      db = re_db.group('db')
      host = (re_user.group('hostname')).lower()      
      instance = re_user.group('instance')  
      
      if 'Error' in version:       
        version = "" 
        self.get_date_formatted()
        f.write(str(formatted) + " - IDOIT - WARNING - Error was found in the output of the version field for " + username + " on database " + database + "\n")
        m.write(str(formatted) + " - IDOIT - WARNING - Error was found in the output of the version field for " + username + " on database " + database + "\n")
      else:
        version = version
      if len(instance) == 1:
        '''
        Call function to update i-doit
        '''      
        self.update_amh(host,f,m,owner,zone,'AMH',instance,version,db)      
      else:
        self.get_date_formatted()
        f.write(formatted + " - IDOIT - ERROR   - Instance of host " + host + " to be checked. Will not be added to i-doit.\n")
        m.write(formatted + " - IDOIT - ERROR   - Instance of host " + host + " to be checked. Will not be added to i-doit.\n")
   
    #-----------------------------------------------------------------------------------------------------------------------------------------#  
    
    def create_amh(self,server_id,app,idoit_api_key,version,instance,db,logfile,maillog,owner):
      create_amh = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\":\"cmdb.object.create\",\"params\":{\"type\":\"C__OBJTYPE__APPLICATION\",\"title\":\"" + app + "\",\"apikey\":\"" + idoit_api_key + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
      amh_result = re.search(r"\"id\": (?P<new_id>\d\d+),", create_amh)
      amh_id = amh_result.group('new_id')
      if 'successfully' in create_amh:
        self.get_date_formatted()
        logfile.write(formatted + " - IDOIT - SUCCESS - Application " + app + " successfully created. Please go to the WebGUI to link this new app with his host\n")
        add_release = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\":\"C__CATG__CUSTOM_FIELDS_VERSION\",\"objID\":" + amh_id + ",\"data\": {\"f_text_c_1555592395597\": \"" + version + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)              
        add_instance = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\":\"C__CATG__CUSTOM_FIELDS_INSTANCE\",\"objID\":" + amh_id + ",\"data\": {\"f_text_c_1555582373221\": \"" + instance + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
        add_db = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"8z7x9i7jz8wsg4g8\",\"category\": \"C__CATG__CUSTOM_FIELDS_DB\",\"objID\": \"" + amh_id + "\",\"data\": {\"f_text_c_1555592236229\": \"" + db + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
        sId = re.search(r"\"(?P<server_id>\d{5,9})\"",server_id)
        server_id = sId.group('server_id')
        add_link = subprocess.check_output("curl -s --data '{\"jsonrpc\": \"2.0\",\"method\": \"cmdb.category.save\",\"params\":{\"object\": " + server_id + ",\"category\": \"C__CATG__APPLICATION\",\"data\": {\"application\": " + amh_id + "},\"apikey\": \"" + idoit_api_key + "\",\"language\": \"en\"},\"id\": \"2\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)         
        add_owner = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\": \"C__CATG__CUSTOM_FIELDS_OWNER\",\"objID\": \"" + amh_id + "\",\"data\": {\"f_text_c_1554902551173\": \"" + owner + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
        if 'successfully' in add_release and 'successfully' in add_instance and 'successfully' in add_db and 'successfully' in add_link :
          self.get_date_formatted()
          logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version added for " + app + "\n")
          logfile.write(str(formatted) + " - IDOIT - SUCCESS - Instance added for " + app + "\n")
          logfile.write(str(formatted) + " - IDOIT - SUCCESS - DB Name added for " + app + "\n")
          logfile.write(str(formatted) + " - IDOIT - SUCCESS - Owner added")
        else:
          self.get_date_formatted()                  
          if 'error' in add_release:
            returned_error_release = re.search(r"\"message\": (?P<error>\"[^*\"]+\")",add_release)
            returned_error_msg = returned_error_release.group('error')            
          elif 'error' in add_instance:
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version added for " + app + "\n")
            returned_error_instance = re.search(r"\"message\": (?P<error>\"[^*\"]+\")",add_instance)
            returned_error_msg = returned_error_instance.group('error') 
          elif 'error' in add_db:
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version added for " + app + "\n")
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - Instance added for " + app + "\n")
            returned_error_instance = re.search(r"\"message\": (?P<error>\"[^*\"]+\")",add_db)
            returned_error_msg = returned_error_instance.group('error') 
          else:
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version added for " + app + "\n")
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - Instance added for " + app + "\n")
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - DB Name added for " + app + "\n")
            returned_error_db = re.search(r"\"message\": (?P<error>\"[^*\"]+\")",add_link)
            returned_error_msg = returned_error_db.group('error') 
          self.get_date_formatted()
          logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + " FOR APP " + app + " WITH VERSION " + version + " WITH INSTANCE " + instance + " AND DB " + db + "\n")  
          maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + " FOR APP " + app + " WITH VERSION " + version + " WITH INSTANCE " + instance + " AND DB " + db + "\n")
      else:
        self.get_date_formatted()
        returned_error_update = re.search(r"\"message\": (?P<error>\"[^*\"]+\")",update_release)
        returned_error_msg = returned_error_update.group('error')                    
        logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + " WHILE CREATING " + app + " WITH VERSION " + version + " WITH INSTANCE " + instance + " AND DB " + db + "\n")
        maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + " WHILE CREATING " + app + " WITH VERSION " + version + " WITH INSTANCE " + instance + " AND DB " + db + "\n")
    
    #-----------------------------------------------------------------------------------------------------------------------------------------#  
    
    def update_amh(self,hostname,logfile,maillog,owner,zone,app=[],instance=[],version=[],db=[]):  
      turn = 0
      
      search = subprocess.check_output("curl -s --data '{\"version\": \"2.0\",\"method\": \"idoit.search\",\"params\": {\"q\": \"" + hostname + "\",\"apikey\": \"" + idoit_api_key + "\",\"language\": \"en\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php", shell=True)
      all_objects = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\":\"cmdb.objects.read\",\"params\":{\"order_by\": \"title\", \"sort\": \"ASC\", \"apikey\":\"" + idoit_api_key + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php",shell=True)
      while turn == 0:
        search = subprocess.check_output("curl -s --data '{\"version\": \"2.0\",\"method\": \"idoit.search\",\"params\": {\"q\": \"" + hostname + "\",\"apikey\": \"" + idoit_api_key + "\",\"language\": \"en\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php", shell=True)
        all_objects = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\":\"cmdb.objects.read\",\"params\":{\"order_by\": \"title\", \"sort\": \"ASC\", \"apikey\":\"" + idoit_api_key + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php",shell=True)   
        if 'value' in search:
          #Get object id
          result = re.search(r"\"documentId\":(?P<id>\"\d\d\d\d\d\")", search)
          
          objId = result.group('id')
          if app in all_objects:
			      #Check if relation exists
            relations = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\": \"cmdb.objects_by_relation\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"Relation_type\": \"C_RELATION_TYPE_APPLICATION\", \"id\":" + objId + "},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php",shell=True)
#            if app in relations:
#              self.get_date_formatted()
#              logfile.write(str(formatted) + " - IDOIT - SUCCESS - " + app + " already linked to " + hostname + " and will be updated\n")
#              if 'AMH' in app and version != None and instance != None and db != None:
#                '''
#                Update AMH application (version and db)
#                '''
#                amh_result = re.search(r"is running " + app + "[^*]*slave\":(?P<slave_id>\d{5,9})", relations)
#                amh_id = amh_result.group('slave_id')
#                existing_instance = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\": \"cmdb.category.read\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\": \"C__CATG__CUSTOM_FIELDS_INSTANCE\",\"objID\": \"" + amh_id + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool | grep f_text",shell=True)
#                exsiting_db = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\": \"cmdb.category.read\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\": \"C__CATG__CUSTOM_FIELDS_DB\",\"objID\": \"" + amh_id + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool | grep f_text",shell=True)
#                new_instance = '"' + instance + '"'
#                if new_instance in existing_instance:
#                  turn += 1
#                  if db in exsiting_db:
#                    update_release = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\":\"C__CATG__CUSTOM_FIELDS_VERSION\",\"objID\":" + amh_id + ",\"data\": {\"f_text_c_1555592395597\": \"" + version + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
#                    if 'successfully' in update_release:
#                      self.get_date_formatted()
#                      logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version updated for " + app + " linked to " + hostname + "\n")
#                    else:
#                      self.get_date_formatted()
#                      returned_error_release = re.search(r"\"message\": (?P<error>\"[^*]*\.\")",update_release)
#                      returned_error_msg = returned_error_release.group('error')       
#                      logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
#                      maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
#                  else:                 
#                    update_release = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\":\"C__CATG__CUSTOM_FIELDS_VERSION\",\"objID\":" + amh_id + ",\"data\": {\"f_text_c_1555592395597\": \"" + version + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True) 
#                    update_db = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"8z7x9i7jz8wsg4g8\",\"category\": \"C__CATG__CUSTOM_FIELDS_DB\",\"objID\": \"" + amh_id + "\",\"data\": {\"f_text_c_1555592236229\": \"" + db + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
#                    if 'successfully' in update_release and 'successfully' in update_db:
#                      self.get_date_formatted()
#                      logfile.write(str(formatted) + " - IDOIT - SUCCESS - Version updated for " + app + " linked to " + hostname + "\n")
#                      logfile.write(str(formatted) + " - IDOIT - SUCCESS - DB Name updated for " + app + " linked to " + hostname + "\n")
#                    else:
#                      self.get_date_formatted()
#                      if 'error' in update_release:
#                        returned_error_release = re.search(r"\"message\": (?P<error>\"[^*]*\.\")",update_release)
#                        returned_error_msg = returned_error_release.group('error')       
#                      else:
#                        returned_error_db = re.search(r"\"message\": (?P<error>\"[^*]*\.\")",update_db)
#                        returned_error_msg = returned_error_db.group('error')   
#                      self.get_date_formatted()
#                      logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
#                      maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
#                else:
#                  '''
#                  Creation of a new instance in i-doit
#                  '''
#                  turn += 1
#                  self.create_amh(objId,app,idoit_api_key,version,instance,db,logfile,maillog,owner)              
#            else:
#              turn += 1
#              self.get_date_formatted()
#              logfile.write(str(formatted) + " - IDOIT - WARNING - " + app + " not related to " + hostname + ". Please add relation via the WebGUI (http://192.168.5.39/i-doit/?viewMode=1001&objTypeID=5)\n")
#              '''
#              Creation of a new instance in i-doit
#              '''
#              self.create_amh(objId,app,idoit_api_key,version,instance,db,logfile,maillog,owner)
#              
                    
          else:
          
            '''
            Creation of new app
            '''
            turn += 1
            self.create_amh(objId,app,idoit_api_key,version,instance,db,logfile,maillog,owner)         
        else:
          '''
          Creation of host
          '''
          self.get_date_formatted()
          logfile.write(str(formatted) + " - IDOIT - WARNING - " + hostname + " does not exist and will be created\n")
          create_host = subprocess.check_output("curl -s --data '{\"jsonrpc\":\"2.0\",\"method\":\"cmdb.object.create\",\"params\":{\"type\":\"C__OBJTYPE__SERVER\",\"title\":\"" + hostname + "\",\"apikey\":\"" + idoit_api_key + "\"},\"id\":1}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
          if 'successfully' in create_host:
            self.get_date_formatted()
            logfile.write(str(formatted) + " - IDOIT - SUCCESS - " + hostname + " has been created\n")            
            hId = re.search(r"\"id\": (?P<host_id>\d{5,9})",create_host)
            new_host_id = hId.group('host_id')
            add_owner = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\": \"C__CATG__CUSTOM_FIELDS_OWNER\",\"objID\": \"" + new_host_id + "\",\"data\": {\"f_text_c_1554902551173\": \"" + owner + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
            add_zone = subprocess.check_output("curl -s --data '{ \"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\": \"cmdb.category.create\",\"params\": {\"apikey\": \"" + idoit_api_key + "\",\"category\": \"C__CATG__CUSTOM_FIELDS_ZONE\",\"objID\": \"" + new_host_id + "\",\"data\": {\"f_text_c_1557325758169\": \"" + zone + "\"}},\"id\": 1,\"version\": \"2.0\"}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
            try:
              host_ip = socket.gethostbyname(hostname)
            except socket.gaierror:
              host_ip = ""
            add_ip = subprocess.check_output("curl -s --data '{\"jsonrpc\": \"2.0\",\"method\": \"cmdb.category.create\",\"params\":{\"objID\": \"" + new_host_id +"\",\"category\": \"C__CATG__IP\",\"data\": {\"net\" : 4343, \"ipv4_address\" : \"" + host_ip + "\"},\"apikey\":\"" + idoit_api_key + "\"},\"id\":2}' --header \"Content-Type: application/json\" http://192.168.5.39/i-doit/src/jsonrpc.php | python -m json.tool",shell=True)
            if 'successfully' in add_ip:
              logfile.write(str(formatted) + " - IDOIT - SUCCESS - IP " + host_ip + " added to host " + hostname + "\n")
            else:
              returned_error_ip = re.search(r"\"message\": (?P<error>\"[^*]*\.\")",add_ip)
              returned_error_msg = returned_error_ip.group('error')
              self.get_date_formatted()
              logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
              maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
           
          else:
            self.get_date_formatted()
            returned_error_create = re.search(r"\"message\": (?P<error>\"[^*]*\.\")",create_host)
            returned_error_msg = returned_error_createe.group('error')       
            self.get_date_formatted()
            logfile.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
            maillog.write(str(formatted) + " - IDOIT - ERROR   - " + returned_error_msg + "\n")
      logfile.close()
      maillog.close()
      
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    def get_date_formatted(self):
      global formatted
      formatted = ""
      date = datetime.now()
      formatted = date.strftime('%Y-%m-%d %H:%M:%S')
    
    #-----------------------------------------------------------------------------------------------------------------------------------------#
    
    
    
    
if __name__ == '__main__':

#  SilApi().push_to_icinga(address,name,os,applications)
  SilApi().amh_automation_update(db,username,version)
  
  
  
  
  
  
  
  
  
  
  
  