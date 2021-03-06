"""Provide IAM Managed policies."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from troposphere import iam, AWSObject

from e3.aws import Construct, name_to_id
from e3.aws.troposphere.iam.policy_document import PolicyDocument

if TYPE_CHECKING:
    from typing import List, Optional


@dataclass(frozen=True)
class ManagedPolicy(Construct):
    """Define a IAM Managed policy.

    :param name: name of the managed policy
    :param roles: list of roles to which this policy is attached
    :param description: managed_policy description    :param description: managed_policy description
    :param users: names (friendly names, not ARN) of users to attach the policy to
    :param groups: names (friendly names, not ARN) of groups to attach the policy to
    :param roles: names (friendly names, not ARN) of roles to attach the policy to
    """

    name: str
    description: Optional[str] = None
    users: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    roles: Optional[List[str]] = None

    # PolicyDocument to attach to this policy
    policy_document: PolicyDocument = field(init=False)

    @property
    def resources(self) -> List[AWSObject]:
        """Return troposphere objects defining the managed policy."""
        attr_policy = {
            key: val
            for key, val in {
                "Description": self.description,
                "Groups": self.groups,
                "ManagedPolicyName": self.name,
                "PolicyDocument": self.policy_document.as_dict,
                "Roles": self.roles,
                "Users": self.users,
            }.items()
            if val is not None
        }
        return [iam.ManagedPolicy.from_dict(name_to_id(self.name), attr_policy)]
