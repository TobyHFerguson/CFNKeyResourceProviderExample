import ptvsd

# Enable ptvsd on 0.0.0.0 address and on port 5890 that we'll connect later with our IDE
ptvsd.enable_attach(address=('0.0.0.0', 5890), redirect_output=True)
ptvsd.wait_for_attach()
breakpoint()

import logging
from typing import Any, MutableMapping, Optional, Mapping

from botocore.exceptions import ClientError

from cloudformation_cli_python_lib import (
    Action,
    HandlerErrorCode,
    OperationStatus,
    ProgressEvent,
    Resource,
    SessionProxy,
    exceptions,
)

from .models import ResourceHandlerRequest, ResourceModel

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)
TYPE_NAME = "toby::EC2::KeyPair"

resource = Resource(TYPE_NAME, ResourceModel)
test_entrypoint = resource.test_entrypoint


@resource.handler(Action.CREATE)
def create_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    # TODO: put code here
    if model.Fingerprint:
        progress.status = OperationStatus.FAILED
        progress.errorCode = HandlerErrorCode.InvalidRequest
        progress.message = "Fingerprint is read-only - should not be specified in a request"
        progress.resourceModel.PublicKey = None
        return progress

    # Example:
    try:
        if isinstance(session, SessionProxy):
            ec2 = session.client('ec2')
            try:
                response = ec2.import_key_pair(
                    KeyName=model.KeyName, PublicKeyMaterial=model.PublicKey)
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "InvalidKeyPair.Duplicate":
                    raise exceptions.AlreadyExists(TYPE_NAME, model.KeyName)
                else:
                    raise
            model.Fingerprint = response['KeyFingerprint']
            model.PublicKey = None
            progress.status = OperationStatus.SUCCESS
            return progress
    except TypeError as e:
        # exceptions module lets CloudFormation know the type of failure that occurred
        raise exceptions.InternalFailure(f"was not expecting type {e}")
        # this can also be done by returning a failed progress event
        # return ProgressEvent.failed(HandlerErrorCode.InternalFailure, f"was not expecting type {e}")
    return progress


# @resource.handler(Action.UPDATE)
# def update_handler(
#     session: Optional[SessionProxy],
#     request: ResourceHandlerRequest,
#     callback_context: MutableMapping[str, Any],
# ) -> ProgressEvent:
#     return create_handler(session, request, callback_context)


@resource.handler(Action.DELETE)
def delete_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:

    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
    )
    
    model.PublicKey = None  # Must not return a write only property
    key_name = request.desiredResourceState.KeyName
    ec2 = session.client('ec2')
    _ = read_handler(session, request, callback_context)
    ec2.delete_key_pair(KeyName=model.KeyName)

    progress.status = OperationStatus.SUCCESS
    return progress


@resource.handler(Action.READ)
def read_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    # Read should not return writeOnlyProperties, and do a full read of the resource
    # See https://github.com/aws-cloudformation/cloudformation-cli/issues/370
    key_name = request.desiredResourceState.KeyName
    ec2 = session.client("ec2")  # type: botostubs.EC2
    try:
        keypairs = ec2.describe_key_pairs(KeyNames=[key_name])["KeyPairs"]
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "InvalidKeyPair.NotFound":
            raise exceptions.NotFound(TYPE_NAME, key_name)
        else:
            # raise the original exception
            raise
    if not len(keypairs) == 1:
        raise exceptions.NotFound(TYPE_NAME, key_name)

    return ProgressEvent(
        status=OperationStatus.SUCCESS, resourceModel=_create_model(
            keypairs[0])
    )


@resource.handler(Action.LIST)
def list_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    ec2 = session.client("ec2")  # type: botostubs.EC2
    keypairs = ec2.describe_key_pairs()["KeyPairs"]

    return ProgressEvent(
        status=OperationStatus.SUCCESS,
        resourceModels=[_create_model(x) for x in keypairs],
    )


def _create_model(o: Mapping) -> ResourceModel:
    return ResourceModel(
        KeyName=o["KeyName"],
        Fingerprint=o["KeyFingerprint"],
        # There is no way to get the PublicKey from the EC2 api.
        # That's why it's defined as a writeOnlyProperty in the resource spec.
        PublicKey=None,
    )
