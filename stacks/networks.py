from aws_cdk import core
import aws_cdk.aws_ec2 as ec2

class Network(core.Stack):

    def __init__(self, scope: core.Construct, id: str, cidr_range: str, add_cidr_range: str, az: str, tgw_asn: int, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC Creation
        self.vpc = ec2.Vpc(self,
            f"{kwargs['env']['region']}-vpc",
            max_azs=3,
            cidr=cidr_range,
            # configuration will create 3 subnets in each of the three AZs.
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.ISOLATED,
                    name="Isolated",
                    cidr_mask=27
                    ),
                ec2.SubnetConfiguration(
                        subnet_type=ec2.SubnetType.PUBLIC,
                        name="Public",
                        cidr_mask=27
                        ),
                ec2.SubnetConfiguration(
                        subnet_type=ec2.SubnetType.PRIVATE,
                        name="Private",
                        cidr_mask=27
                        )
            ]
        )

        self.vpc_add_cidr = ec2.CfnVPCCidrBlock(self, 
            id=f"{kwargs['env']['region']}-vpc-tgw-cidr", 
            vpc_id=self.vpc.vpc_id,
            cidr_block=add_cidr_range
            )

        self.tgw_subnet_a = ec2.CfnSubnet(self,
            id=f"{kwargs['env']['region']}-tgw-sub-1a",
            cidr_block=add_cidr_range.replace('/24','/26'),#100.64.x.0/26
            vpc_id=self.vpc.vpc_id,
            availability_zone=az
        ).add_depends_on(self.vpc_add_cidr)

        self.tgw_subnet_b = ec2.CfnSubnet(self,
            id=f"{kwargs['env']['region']}-tgw-sub-1b",
            cidr_block=add_cidr_range.replace('.0/24','.64/26'),#100.64.x.64/26
            vpc_id=self.vpc.vpc_id,
            availability_zone=az.replace('-1a','-1b')
        ).add_depends_on(self.vpc_add_cidr)

        # self.tgw_subnet_rt = ec2.CfnRouteTable(self,
        #     id=f"{kwargs['env']['region']}-tgw-rt",
        #     vpc_id=self.vpc.vpc_id,
        # )

        # self.tgw_subnet_route = ec2.CfnRoute(self,
        #     id=f"{kwargs['env']['region']}-tgw-route",
        #     route_table_id=self.tgw_subnet_route.route_table_id,
        #     transit_gateway_id='todo',
        #     destination_cidr_block='0.0.0.0/0'
        # )

        # self.tgw_subnet_rt_assoc = ec2.CfnSubnetRouteTableAssociation(self,
        #     id=f"{kwargs['env']['region']}-tgw-rt-assoc",
        #     route_table_id=self.tgw_subnet_rt,
        #     subnet_id=self.tgw_subnet_a
        # ).add_depends_on()

        # self.tgw_subnet_rt_assoc = ec2.CfnSubnetRouteTableAssociation(self,
        #     id=f"{kwargs['env']['region']}-tgw-rt-assoc",
        #     route_table_id=self.tgw_subnet_rt,
        #     subnet_id=self.tgw_subnet_b
        # ).add_depends_on()

        # Transit Gateway creation
        self.tgw = ec2.CfnTransitGateway(
            self,
            id=f"TGW-{kwargs['env']['region']}",
            amazon_side_asn=tgw_asn,
            auto_accept_shared_attachments="enable",
            default_route_table_association="enable",
            default_route_table_propagation="enable",
            tags=[core.CfnTag(key='Name', value=f"tgw-{kwargs['env']['region']}")]
        )

        # Transit Gateway attachment to the VPC
        self.tgw_attachment = ec2.CfnTransitGatewayAttachment(
            self,
            id=f"tgw-vpc-{kwargs['env']['region']}",
            transit_gateway_id=self.tgw.ref,
            vpc_id=self.vpc.vpc_id,
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.isolated_subnets],
            tags=[core.CfnTag(key='Name', value=f"tgw-{self.vpc.vpc_id}-attachment")]
        )

        # VPC Endpoint creation for SSM (3 Endpoints needed)
        # ec2.InterfaceVpcEndpoint(
        #     self,
        #     "VPCe - SSM",
        #     service=ec2.InterfaceVpcEndpointService(
        #         core.Fn.sub("com.amazonaws.${AWS::Region}.ssm")
        #     ),
        #     private_dns_enabled=True,
        #     vpc=self.vpc,
        # )

        # ec2.InterfaceVpcEndpoint(
        #     self,
        #     "VPCe - EC2 Messages",
        #     service=ec2.InterfaceVpcEndpointService(
        #         core.Fn.sub("com.amazonaws.${AWS::Region}.ec2messages")
        #     ),
        #     private_dns_enabled=True,
        #     vpc=self.vpc,
        # )

        # ec2.InterfaceVpcEndpoint(
        #     self,
        #     "VPCe - SSM Messages",
        #     service=ec2.InterfaceVpcEndpointService(
        #         core.Fn.sub("com.amazonaws.${AWS::Region}.ssmmessages")
        #     ),
        #     private_dns_enabled=True,
        #     vpc=self.vpc,
        # )
