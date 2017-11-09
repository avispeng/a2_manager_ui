ami_id = 'ami-da8b3da0'
instance_type = 't2.small'
key_name = 'A1_Web_Development'
security_group = ['sg-c3cb97b1']
elbname = 'ece1779lb'
iam_instance_profile = {'Arn':'arn:aws:iam::770147457029:instance-profile/a2worker'}
# 'Name':'a2worker'
monitoring = {'Enabled':True}
subnet = 'subnet-311b0e1d'
tag_specification = [{
                        'ResourceType':'instance',
                        'Tags':[
                            {
                                'Key':'Name',
                                'Value':'worker'
                            }
                        ]}]
userdata = """
#cloud-config
runcmd:
 - cd /home/ubuntu/Desktop/ece1779/a2/A1_web_development
 - chmod +x ./run.sh
 - sudo ./run.sh

output : { all : '| tee -a /var/log/cloud-init-output.log' }
"""

# remote testing
# db_config = {'user': 'ece1779',
#              'password': 'secret',
#              'host': '172.31.82.184',
#              'database': 'photo_browser'}

db_config = {'user': 'ece1779',
             'password': 'secret',
             'host': 'localhost',
             'database': 'photo_browser'}

# cpu_threshold_high = 0.6
# cpu_threshold_low = 0.3
# ratio_grow = 2
# ratio_shrink = 4