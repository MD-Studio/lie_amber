# -*- coding: utf-8 -*-

import os
import shutil

from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession
from lie_amber.ambertools import (amber_acpype, amber_reduce)


def encoder(file_path):
    """
    Encode the content of `file_path` into a simple dict.
    """
    extension = os.path.splitext(file_path)[1]
    with open(file_path, 'r') as f:
        content = f.read()

    return {"path": file_path, "extension": extension.lstrip('.'),
            "content": content, "encoding": "utf8"}


def encode_file(val):
    if not os.path.isfile(val):
        return val
    else:
        return encoder(val)


class AmberWampApi(ComponentSession):
    """
    AmberTools WAMP methods.
    """
    def authorize_request(self, uri, claims):
        return True

    @endpoint('acpype', 'acpype_request', 'acpype_response')
    def run_amber_acpype(self, request, claims):
        """
        Call amber acpype package using a molecular `structure`.
        See the `schemas/endpoints/acpype-request.v1.json for
        details.
        """
        # Load ACPYPE configuration and update
        acpype_config = get_amber_config(request)
        result = call_amber_package(request, acpype_config, amber_acpype)

        return {key: encode_file(val) for key, val in result.items()}

    @endpoint('reduce', 'reduce_request', 'reduce_response')
    def run_amber_reduce(self, request, claims):
        """
        Call amber reduce using a  a molecular `structure`.
        See the the `schemas/endpoints/reduce-request.v1.json for
        details.
        """
        reduce_config = get_amber_config(request)
        result = call_amber_package(request, reduce_config, amber_reduce)

        return {key: encode_file(key, val) for key, val in result.items()}


def get_amber_config(request):
    """
    Remove the keywords not related to amber
    """
    d = request.copy()
    keys = ['workdir', 'structure', 'from_file']

    for k in keys:
        if k in d:
            d.pop(k)

    return d


def call_amber_package(request, config, function):
    """
    Create temporate files and invoke the `function` using `config`.
    """
    # Create workdir and save file
    workdir = os.path.abspath(request['workdir'])
    create_dir(workdir)
    tmp_file = create_temp_file(
        request['structure']['content'], request['from_file'], workdir)

    # Run amber function
    output = function(tmp_file, config, workdir)
    return output


def copy_structure(structure, from_file, tmp_file):
    if from_file and os.path.exists(structure):
        shutil.copyfile(structure, tmp_file)
    else:
        with open(tmp_file, 'w') as inp:
            inp.write(structure)


def create_dir(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)


def create_temp_file(structure, from_file, workdir):
    tmp_file = os.path.join(workdir, 'input.mol2')
    copy_structure(structure, from_file, tmp_file)

    return tmp_file


def read_file(path):
    if os.path.isfile(path):
        with open(path, "r") as f:
            return f.read()
    else:
        return path
