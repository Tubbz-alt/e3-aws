import requests
from e3.aws.cfn.ec2.security import Ipv4EgressRule, SecurityGroup

# This is the static address at which AWS publish the list of ip-ranges
# used by its services.
IP_RANGES_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"


def amazon_security_groups(name, vpc):
    """Create a dict of security group authorizing access to aws services.

    As the number of rules per security group is limited to 50,
    we create blocks of 50 rules.

    :param vpc: vpc in which to create the group
    :type vpc: VPC
    :return: a dict of security groups indexed by name
    :rtype: dict(str, SecurityGroup)
    """

    def select_region(ip_range_record):
        """Select the VPN region and the us-east-1 region.

        Note that some global interface (e.g. sts) are only available in
        the us-east-1 region.
        """
        return ip_range_record["region"] in (vpc.region, "us-east-1")

    ip_ranges = requests.get(IP_RANGES_URL).json()["prefixes"]

    # Retrieve first the complete list of ipv4 ip ranges for a given region
    amazon_ip_ranges = {
        k["ip_prefix"]
        for k in ip_ranges
        if select_region(k) and "ip_prefix" in k and k["service"] == "AMAZON"
    }

    # Sustract the list of ip ranges corresponding to EC2 instances
    ec2_ip_ranges = {
        k["ip_prefix"]
        for k in ip_ranges
        if select_region(k) and "ip_prefix" in k and k["service"] == "EC2"
    }
    amazon_ip_ranges -= ec2_ip_ranges

    # Authorize https on the resulting list of ip ranges
    sgs = {}
    i = 0
    limit = 60
    sg_name = name + str(i)
    sg = SecurityGroup(sg_name, vpc, description="Allow access to amazon services")
    sgs[sg_name] = sg
    for ip_range in amazon_ip_ranges:
        if len(sg.egress + sg.ingress) == limit:
            i += 1
            sg_name = name + str(i)
            sg = SecurityGroup(
                sg_name, vpc, description="Allow acces to amazon services"
            )
            sgs[sg_name] = sg
        sg.add_rule(Ipv4EgressRule("https", ip_range))
    return sgs


def github_security_groups(name, vpc, protocol):
    """Create a dict of security group authorizing access to github services.

    As the number of rules per security group is limited to 50,
    we create blocks of 50 rules.

    :param vpc: vpc in which to create the group
    :type vpc: VPC
    :param protocol: protocol to allow (https, ssh)
    :type protocol: str
    :return: a dict of security groups indexed by name
    :rtype: dict(str, SecurityGroup)
    """
    ip_ranges = requests.get("https://api.github.com/meta").json()["git"]

    # Authorize ssh on the resulting list of ip ranges
    sgs = {}
    i = 0
    limit = 50
    sg_name = name + str(i)
    sg = SecurityGroup(sg_name, vpc, description="Allow access to github")
    sgs[sg_name] = sg
    for ip_range in ip_ranges:
        if len(sg.egress + sg.ingress) == limit:
            i += 1
            sg_name = name + str(i)
            sg = SecurityGroup(
                sg_name, vpc, description=f"Allow access to GitHub {protocol}"
            )
            sgs[sg_name] = sg
        sg.add_rule(Ipv4EgressRule(protocol, ip_range))
    return sgs
