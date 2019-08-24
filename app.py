#!/usr/bin/env python3

from aws_cdk import core
from dotenv import load_dotenv

from cdk.vpn_stack import VpnStack

load_dotenv(verbose=True)

app = core.App()
VpnStack(app, "vpn-cdk")

app.synth()
