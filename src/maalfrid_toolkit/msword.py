import subprocess

import docx2txt
import os
import re

mime_extensions = {'application/msword': '.doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx', 'application/vnd.oasis.opendocument.text-master': '.odt'}


def _extract_text_from_doc(file_path):
    try:
        result = subprocess.run(['antiword', file_path], capture_output=True, text=True)
        return result.stdout
    except FileNotFoundError:
        print("antiword is not installed. Please install it first.")
        raise e
    except Exception as e:
        raise e
    
def _extract_text_from_docx(file_path) -> str:
    return docx2txt.process(file_path)

def extract_doc_from_file(filepath):
    if filepath.endswith(".doc"):
        return _extract_text_from_doc(filepath)
    elif filepath.endswith(".docx"):
        return _extract_text_from_docx(filepath)
    else:
        raise Exception("Can only process .doc or .docx formats")

def extract_doc(urn, content_stream, mime_type="application/msword"):
    urn = urn.replace("<urn:uuid:", "")
    urn = urn.replace(">", "")

    # look for the beginning of the mime type to catch cases like "application/vnd.openxmlformats-officedocument.wordprocessingml.document; charset=utf-8"
    matching_extension = next((ext for key, ext in mime_extensions.items() if mime_type.startswith(key)), None)

    # if a match was found, write to a temp file
    if matching_extension:
        temppath = "/tmp/" + urn + matching_extension
    else:
        return None

    try:
        with open(temppath, 'wb') as tempfile:
            tempfile.write(content_stream)
    except:
        print("could not create tempfile", urn)
        return None
    try:
        text = extract_doc_from_file(temppath)
    except:
        print("could not extract content", urn)
        return None
    finally:
        try:
            os.remove(temppath)
        except:
            pass

    # Postgres does not handle the NULL character (\x00), replace it with "replacement character"
    # https://github.com/cms-dev/cms/issues/888
    text = text.replace("\x00", "\uFFFD")

    # remove empty lines
    text = re.sub(r'\n+', '\n', text)

    # trim spaces and newlines on beginning and end of string
    text = text.strip()

    return text
