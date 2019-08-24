import os
from typing import List

from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk import core


class VpnStack(core.Stack):

    def _add_role(self) -> iam.Role:
        """
        Add IAM role to the stack
        """
        role = iam.Role(
            self, 'VPNInstanceRole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com')
        )
        # add access to outputs of the current stack to ec2 instance
        role.add_to_policy(
            iam.PolicyStatement(
                resources=[self.format_arn(resource="stack/vpn-cdk/*", service="cloudformation")],
                actions=['cloudformation:*']
            ))
        # add policy to allow elastic ip association
        role.add_to_policy(
            iam.PolicyStatement(
                resources=['*'],
                actions=['ec2:AssociateAddress']
            )
        )
        return role

    def _create_public_subnet(self) -> ec2.SubnetConfiguration:
        """
        Configure a public subnet
        """
        return ec2.SubnetConfiguration(
            name='vpn-application',
            subnet_type=ec2.SubnetType.PUBLIC,
        )

    def _add_vpc(self, subnets: List[ec2.SubnetConfiguration]) -> ec2.Vpc:
        """
        Add VPC to the stack
        :param subnets: list of available subnets
        """
        return ec2.Vpc(
            self,
            'vpn-vpc',
            cidr='10.1.0.0/24',
            subnet_configuration=subnets
        )

    def _add_security_groups(self, vpc: ec2.Vpc) -> ec2.SecurityGroup:
        """
        Add security group to the stack
        :param vpc: VPC of security group
        """
        security_group = ec2.SecurityGroup(
            self,
            'vpn-security-group',
            vpc=vpc,
            description="Allow access to vpn instance",
            allow_all_outbound=True
        )
        if os.environ.get('EC2_SSH_ALLOWED', False):
            security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(22),
                'allow ssh access from the world'
            )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.udp(500),
            'for IKE, to manage encryption keys'
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.udp(4500),
            'for IPSEC NAT-Traversal mode'
        )
        return security_group

    def _add_ssm_parameters(self, role: iam.Role):
        """
        Copy environment variables to Param Store
        :param role: add permission to role for accessing parameters in Param Store
        """
        params = [
            {'env_param': 'VPN_IPSEC_PSK', 'description': 'The IPsec PSK (pre-shared key)'},
            {'env_param': 'VPN_USER', 'description': 'The VPN username'},
            {'env_param': 'VPN_PASSWORD', 'description': 'The VPN password'},
            {'env_param': 'VPN_ADDL_USERS', 'description': 'Additional VPN usernames'},
            {'env_param': 'VPN_ADDL_PASSWORDS', 'description': 'Additional VPN password'},
            {'env_param': 'VPN_DNS_SRV1', 'description': 'Alternative DNS servers #1'},
            {'env_param': 'VPN_DNS_SRV2', 'description': 'Alternative DNS servers #2'},

        ]

        for p in params:
            if os.environ.get(p['env_param']):
                param_id = ''.join([w.lower().capitalize() for w in p['env_param'].split('-')])
                param = ssm.StringParameter(
                    self, param_id,
                    parameter_name="/cdk-vpn/{}".format(p['env_param']),
                    description=p['description'],
                    string_value=os.environ[p['env_param']]
                )
                # grant read access to role
                param.grant_read(role)

    def _add_autoscaling_group(
            self,
            vpc: ec2.Vpc,
            public_subnet: ec2.SubnetConfiguration,
            security_group: ec2.SecurityGroup,
            role: iam.Role) -> autoscaling.AutoScalingGroup:
        """
        Add autoscaling group for running ec2 instance automatically
        """
        group = autoscaling.AutoScalingGroup(
            self,
            'vpn-autoscale',
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=ec2.AmazonLinuxImage(),
            max_capacity=1,
            vpc_subnets=public_subnet,
            associate_public_ip_address=True,
            key_name='vpn-key',
            role=role
        )
        group.add_security_group(security_group)
        return group

    def _add_bootstrap_script_to_ec2(self, group: autoscaling.AutoScalingGroup):
        """
        Copy boostrap script to user data. Ec2 instance runs this script during initialization
        """
        with open('bootstrap.sh', 'r') as f:
            commands = [l for l in f.readlines()[1:] if l.strip()]
        group.add_user_data(
            *commands
        )

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # add elastic IP to the stack
        elastic_ip = ec2.CfnEIP(self, "vpn-elastic-ip")

        # create public subnet to place ec2 instance for public access
        public_subnet = self._create_public_subnet()

        # create a role associated with vpc instance
        role = self._add_role()

        # add vpn config to ssm parameters
        self._add_ssm_parameters(role)

        # create vpc with public subnet
        vpc = self._add_vpc([public_subnet])

        # add security group
        security_group = self._add_security_groups(vpc)

        # add autoscaling group
        autoscaling_group = self._add_autoscaling_group(vpc, public_subnet, security_group, role)

        # add bootstrap script
        self._add_bootstrap_script_to_ec2(autoscaling_group)

        # publish resource output
        core.CfnOutput(
            self, "AllocationId",
            description="The ID that AWS assigns to represent the allocation of the address for use with Amazon VPC. "
                        "This is returned only for VPC elastic IP addresses. For example, eipalloc-5723d13e.",
            value=elastic_ip.get_att('AllocationId').to_string()
        )
