from app.manager_ui import cpu_load, get_global

from app import config
from app import webapp
import boto3
import math
import time

import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


@webapp.route('/auto_refresh')
def auto_refresh():

    cpu_threshold_high, cpu_threshold_low, ratio_grow, ratio_shrink= get_global()
    response=None
    # create connection to ec2 worker pool
    ec2 = boto3.resource('ec2')
    # list a list of instances named 'worker'
    workers = ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': ['worker']},
                                            {'Name': 'instance-state-name',
                                             'Values': ['running']}])
    cpu_sum = 0
    count = 0
    average_current = (cpu_threshold_low + cpu_threshold_high) / 2
    for instance in workers:
        cpu_sum += cpu_load(instance.id)[0]
        count += 1
    if count > 0:
        average_current = cpu_sum / count
    if average_current >= cpu_threshold_high:
        num_to_grow = math.floor(ratio_grow * count - count)
        if num_to_grow > 0:
            new_instances = ec2.create_instances(ImageId=config.ami_id,
                                                MinCount=num_to_grow,
                                                MaxCount=num_to_grow,
                                                InstanceType=config.instance_type,
                                                KeyName=config.key_name,
                                                Monitoring=config.monitoring,
                                                SecurityGroupIds=config.security_group,
                                                SubnetId=config.subnet,
                                                UserData=config.userdata,
                                                IamInstanceProfile=config.iam_instance_profile,
                                                TagSpecifications=config.tag_specification
                                                )
            # collect their ids
            new_ids = []
            ids_desc = []
            for new_worker in new_instances:
                new_ids.append({'InstanceId':new_worker.id})
                ids_desc.append(new_worker.id)

            # exp backoff
            ec2_client = boto3.client('ec2')
            wait = 1
            while wait <= 10:
                try:
                    response = ec2_client.describe_instances(InstanceIds=ids_desc)
                    print("described")
                    break
                except Exception:
                    print("wait for",wait,"s")
                    time.sleep(wait)
                    wait += 1
                    continue

            # attach them to load balancer
            elb = boto3.client('elb')
            response = elb.register_instances_with_load_balancer(
                LoadBalancerName=config.elbname,
                Instances=new_ids
            )
            # MAIN_MSG = 'Automatically expanded the worker pool by ratio '+str(ratio_grow)
    elif average_current <= cpu_threshold_low:
        num_to_shrink = math.floor(count - count * 1. / ratio_shrink)
        if num_to_shrink > 0 and count > 1:
            elb = boto3.client('elb')
            delete_ids = []
            for worker in workers:
                delete_ids.append({'InstanceId': worker.id})
                worker.terminate()
                num_to_shrink -= 1
                if num_to_shrink == 0:
                    break
            # detach from load balancer
            response = elb.deregister_instances_from_load_balancer(
                LoadBalancerName=config.elbname,
                Instances=delete_ids
            )
            # MAIN_MSG = 'Automatically shrank the worker pool by ratio ' + str(ratio_shrink)
    #return redirect(url_for('main'))
    print(response)
    print(cpu_threshold_high, cpu_threshold_low, ratio_grow, ratio_shrink)
    return response

# if __name__ == '__main__':

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=auto_refresh,
    trigger=IntervalTrigger(seconds=60),
    id='worker_list',
    name='Refresh the worker pool every 60 seconds',
    misfire_grace_time=10,
    coalesce=True,
    max_instances=1,
    replace_existing=False)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

