import json
import pathlib as pt
from collections import UserDict
from typing import Dict, Union

import yaml


class EncryptedDict(UserDict):
    def dump(self, fpath: pt.Path) -> None:
        def convert_to_hex(dictionary: dict, hexed_dict: dict):
            for k in dictionary:
                item: bytes = dictionary[k]
                if isinstance(item, bytes):
                    hexed = item.hex()
                    hexed_dict[k.hex()] = hexed
                else:
                    converted_dict = convert_to_hex(dictionary[k], {})
                    hexed_dict[k.hex()] = converted_dict
            return hexed_dict

        hex_dict = convert_to_hex(self.copy(), {})

        with open(fpath, "w") as handle:
            json.dump(hex_dict, handle)


def run(
    string_or_path: Union[str, pt.Path],
    rsa_helper: "RSA",
    file_parser,
    dictionary_parser,
):
    if any([isinstance(string_or_path, T) for T in (str, pt.Path)]):
        string_or_path = pt.Path(string_or_path)

        assert string_or_path.is_file(), (
            "%s must be a file or dictionary" % string_or_path
        )
        assert string_or_path.exists(), (
            "file %s does not exists" % string_or_path
        )

        return file_parser(string_or_path, rsa_helper)

    elif any([isinstance(string_or_path, T) for T in [dict, EncryptedDict]]):
        return dictionary_parser(string_or_path, rsa_helper)

    else:
        raise TypeError(
            "%s must be either a dictionary or path" % string_or_path
        )


def encrypt(
    not_encrypted: Union[str, pt.Path, dict], rsa_helper: "RSA"
) -> EncryptedDict:
    def dictionary(d: dict, helper: "RSA") -> EncryptedDict:
        output = {}
        for k, s in d.items():
            k_encrypted = helper.encrypt(k)

            if isinstance(s, str):
                s_encrypted = helper.encrypt(s)
                output[k_encrypted] = s_encrypted
            elif isinstance(s, dict):
                output[k_encrypted] = dictionary(s, helper)
            else:
                raise TypeError("d must either be a string not %s" % s)

        return EncryptedDict(output)

    def file(fpath: Union[str, pt.Path], helper: "RSA") -> EncryptedDict:
        with open(fpath, "r") as f:
            contents = yaml.safe_load(f)
        return dictionary(contents, helper)

    return run(not_encrypted, rsa_helper, file, dictionary)


def decrypt(
    encrypted: Union[str, pt.Path, dict], rsa_helper: "RSA"
) -> Dict["Dict[str]", str]:
    def dictionary(d: dict, helper: "RSA") -> Dict["Dict[str]", str]:
        output = {}
        for k, s in d.items():
            k_decrypted = helper.decrypt(k)

            if isinstance(s, bytes):
                s_decrypted = helper.decrypt(s)
                output[k_decrypted] = s_decrypted
            elif any([isinstance(s, t) for t in (dict, EncryptedDict)]):
                output[k_decrypted] = dictionary(s, helper)
            else:
                raise TypeError(
                    "d must either be a string or dictionary not %s"
                    % s.__class__
                )

        return output

    def file(
        f: Union[str, pt.Path], helper: "RSA"
    ) -> Dict[Dict[str, str], str]:
        def convert_to_bytes(dictionary: dict, bytes_dict: dict):
            for k in dictionary:
                item: str = dictionary[k]
                if isinstance(item, str):
                    bytes_hex = bytes.fromhex(item)
                    bytes_dict[bytes.fromhex(k)] = bytes_hex
                else:
                    converted_dict = convert_to_bytes(dictionary[k], {})
                    bytes_dict[bytes.fromhex(k)] = converted_dict
            return bytes_dict

        f = pt.Path(f)
        assert f.suffix in [".dbqq"], "%s is not a dbqq file" % f
        with open(f, "r") as f:
            configs = json.load(f)
        configs = convert_to_bytes(configs, {})
        return dictionary(configs, rsa_helper)

    return run(encrypted, rsa_helper, file, dictionary)
