# IPsec VPN Server on AWS CDK  

Deployment of hwdsl2/docker-ipsec-vpn-server docker image on Amazon Web Services using AWS CDK

![architecture diagram][logo]


## Table of Contents

- [Getting Started](#getting-started) 
    - [Prerequisites](#prerequisites)
    - [Deployment](#deployment)
- [Next Steps](#next-steps)
- [License](#license)
- [Acknowledgments](#acknowledgments)    

## Getting Started

### Prerequisites

- python >= 3.6
- pip or [pipenv]
- [aws-cdk]

### Deployment

1. Install python requirements:

    - Using pip:
    ```
    pip install -r requirements.txt
    ```
    - pipenv users:
    ```
    pipenv install
    ```
1. Configure vpn.env (see [vpn.env.example](vpn.env.example) for reference)
1. To review an AWS CloudFormation template run:
    ```
    cdk synth 
    ```
1. To deploy the stack into an AWS account run:
    ```
    cdk deploy
    ``` 
1.  Stack associates Elastic IP with EC2 instance. Check AWS Console to find out a Public IP address or run:
    ```
    aws ec2 describe-addresses --allocation-ids $(aws cloudformation describe-stacks --stack-name vpn-cdk --query "Stacks[0].Outputs[?OutputKey=='AllocationId'].OutputValue" --output text) | grep 'PublicIp"'
    ```
1. To destroy the stack run:
    ```
    cdk destroy
    ```
    
## Next Steps

1. Get your computer or device to use the VPN. Please refer to:
    https://github.com/hwdsl2/docker-ipsec-vpn-server#next-steps   
1. For iOS users check out:   
    [iOS VPN auto-connect mobileconfig file generator]
    
    
## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

Check [hwdsl2/docker-ipsec-vpn-server] for details of the deployed docker container
 

[logo]: docs/vpn-diag.png "Architecture diagram"
[hwdsl2/docker-ipsec-vpn-server]: https://github.com/hwdsl2/docker-ipsec-vpn-server "docker"
[aws-cdk]: https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html "cdk installation"
[pipenv]: https://github.com/pypa/pipenv "pipenv"
[iOS VPN auto-connect mobileconfig file generator]: https://github.com/klinquist/iOS-VPN-Autoconnect