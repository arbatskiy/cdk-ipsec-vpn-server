#!/bin/bash

# update package manager and install system packages
sudo yum update -y
sudo yum install -y jq docker

# get aws region of the current instance
AWS_DEFAULT_REGION=$(curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
echo "Current region ${AWS_DEFAULT_REGION}"
# get instance id
instance_id=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance id: $instance_id"
# get allocation id of elastic IP
allocation_id=$(aws cloudformation describe-stacks --stack-name vpn-cdk --region $AWS_DEFAULT_REGION --query "Stacks[0].Outputs[?OutputKey=='AllocationId'].OutputValue" --output text)
echo "Allocation id: ${allocation_id}"
# associate elastic ip with instance
aws ec2 associate-address --region ${AWS_DEFAULT_REGION} --allocation-id ${allocation_id} --instance-id $instance_id

# load environment variables from Param Store
for param_name in VPN_IPSEC_PSK VPN_USER VPN_PASSWORD VPN_ADDL_USERS VPN_ADDL_PASSWORDS
do
    export $param_name=$(aws --region=us-east-1 ssm get-parameter --name "/cdk-vpn/$param_name" --with-decryption --output text --query Parameter.Value || "")
done

# start docker server
sudo service docker start

# start ipsec vpn container in daemon mode, always restart
sudo docker run -e "VPN_IPSEC_PSK=${VPN_IPSEC_PSK}" -e "VPN_USER=${VPN_USER}" -e "VPN_PASSWORD=${VPN_PASSWORD}" -e "VPN_ADDL_USERS=${VPN_ADDL_USERS}" -e "VPN_ADDL_PASSWORDS=${VPN_ADDL_PASSWORDS}" --restart=always -p 500:500/udp -p 4500:4500/udp --privileged -d hwdsl2/ipsec-vpn-server

