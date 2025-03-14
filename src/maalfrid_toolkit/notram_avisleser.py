import argparse
import faulthandler
import io
import logging
import os
import re
import signal
import statistics
import string
import sys
import tarfile
import traceback
from collections import Counter
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, NoReturn, Optional, Tuple, Any, Union
# import warnings; warnings.filterwarnings("ignore")

from joblib import Parallel, delayed
from joblib import Memory

import fitz
from pdfminer.high_level import extract_pages, extract_text_to_fp
from pdfminer.layout import LTTextContainer, LTAnno, LTChar, LAParams, LTPage
from sentence_splitter import SentenceSplitter, split_text_into_sentences
from tqdm import tqdm


"""
==========================================================================================

Forked/copied from:
https://github.com/NbAiLab/notram/tree/master/pdfa_parser

                   Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2021 National Library of Norway
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

==========================================================================================
"""


SPACES_RE = re.compile(r"[ ][ ]+")
STARTEND_RE = re.compile(r"(\n\s+)")
HYPHENS_RE = re.compile(r"([a-zæåø])-\s+([a-zæåø])")
HYPHENSHASH_RE = re.compile(r"([a-zæåø])-#\s+([a-zæåø])")
LINEBREAK_RE = re.compile(r"[\n]")
LINEBREAKS_RE = re.compile(r"[\n]{2,}")
SPLITTER = SentenceSplitter(language='no')
LOGGER = None
NOW = datetime.now()

class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds, description=None):
    def signal_handler(signum, frame):
        raise TimeoutException(description or "Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def get_logger() -> logging.Logger:
    """
    Get a logger
    """
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger(__name__)
        LOGGER.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d - %H:%M:%S"
        )
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        LOGGER.addHandler(console)
    return LOGGER


def process_text_container(element: LTTextContainer) -> Tuple[List[str], float]:
    fontnames = []
    fontsize = 0
    if isinstance(element, Iterable):
        for text_line in element:
            if isinstance(text_line, Iterable):
                for character in text_line:
                    if isinstance(character, LTChar):
                        fontnames.append((character.fontname, character.size))
                        if fontsize < character.size:
                            fontsize = character.size
            elif isinstance(text_line, LTChar):
                fontnames.append((text_line.fontname, text_line.size))
                if fontsize < text_line.size:
                    fontsize = text_line.size
    elif isinstance(element, LTChar):
        fontnames.append((element.fontname, element.size))
        if fontsize < element.size:
            fontsize = element.size
    return fontnames, fontsize


def traverse(element: Union[Iterable, LTTextContainer]) -> Tuple[List[str], float]:
    fontnames = []
    fontsize = 0
    if isinstance(element, LTTextContainer):
        return process_text_container(element)
    elif isinstance(element, Iterable):
        for item in element:
            element_output = traverse(item)
            if element_output:
                element_fontnames, element_fontsize = element_output
                fontnames += element_fontnames
                if fontsize < element_fontsize:
                    fontsize = element_fontsize
    return fontnames, fontsize


def get_most_frequent_and_largest_fonts(
    pages: List[LTPage]
) -> Tuple[str, float]:
    all_fonts, fontsize = traverse(pages)
    fontnames = Counter(all_fonts)
    return (
        fontnames.most_common(1)[0][0][0] if fontnames else None,
        fontnames.most_common(1)[0][0][1] if fontnames else None,
        fontsize if fontsize > 0 else None
    )


def get_text_containers(element: Any) -> List[LTTextContainer]:
    containers = []
    if isinstance(element, LTTextContainer):
        return [element]
    elif isinstance(element, Iterable):
        for item in element:
            element_output = get_text_containers(item)
            if element_output:
                containers += element_output
    return containers


def get_text_line(
    text_line: List,
    line_number: int,
    font: str,
    size: float,
    previous_line_font: str,
) -> str:
    chars = ""
    line_font = ""
    if isinstance(text_line, Iterable):
        for character_number, character in enumerate(text_line):
            char = " "
            if isinstance(character, LTChar):
                char_font = getattr(character, "fontname")
                char_size = getattr(character, "size")
                if char_font == font or char_size == size:
                    char = character.get_text()
                # TODO: Identify subheadings
                # if (getattr(character, "fontname") != font
                #     and getattr(character, "fontname") != previous_line_font
                #     and getattr(character, "size") == size
                #     and line_number == 0
                #     and character_number == 0):
                #     char = f"\n→ {char}"
                # char += character.get_text()
                if char.strip():
                    line_font = getattr(character, "fontname", "")
            chars = f"{chars}{char}"
    else:
        try:
            chars = text_line.get_text()
        except:
            pass
    return chars, line_font


def get_text(
    pages: List[LTPage],
    font: str,
    size: float,
    page_break: Optional[str]=None,
) -> str:
    text = ""
    for page_layout in pages:
        for box_id, element in enumerate(page_layout):
            if isinstance(element, LTTextContainer):
                last_font = ""
                for line_number, text_line in enumerate(element):
                    chars, last_font = get_text_line(text_line, line_number, font, size, last_font)
                    text = f"{text} {chars} "
                text = f"{text}\n"
        if page_break and text.strip():
            text = f"{text}{page_break}"
    return text


def get_unstructured_text(
    pages: List[LTPage],
    font: str,
    size: float,
    page_break: Optional[str]=None,
) -> str:
    text = ""
    for element in get_text_containers(pages):
        last_font = ""
        for line_number, text_line in enumerate(element):
            chars, last_font = get_text_line(text_line, line_number, font, size, last_font)
            text = f"{text} {chars} "
        text = f"{text}\n"
        if page_break and text.strip():
            text = f"{text}{page_break}"
    return text


def get_all_texts(
    filename: Union[str, Path],
    line_margin: float=0.15,
    detect_vertical: bool=-0.8,
    boxes_flow: Optional[float]=None,
    page_break: Optional[str]=None,
) -> str:
    laparams = LAParams(
        line_margin=line_margin,
        boxes_flow=boxes_flow,
        detect_vertical=detect_vertical,
        all_texts=True,
    )
    pages = list(extract_pages(filename, laparams=laparams))
    font, size, _ = get_most_frequent_and_largest_fonts(pages)
    text = get_unstructured_text(pages, font, size, page_break)
    if text.strip():
        return text, None
    with open(filename, 'rb') as file, io.StringIO() as buffer:
        extract_text_to_fp(file, buffer, laparams=laparams)
        text = buffer.getvalue().strip()
    html = None  # disabling HTML for now
    # with open(filename, 'rb') as file, io.StringIO() as buffer:
    #     extract_text_to_fp(
    #         file, buffer, laparams=laparams, output_type='html', codec=None
    #     )
    #     html = buffer.getvalue().strip()
    # return LINEBREAK_RE.sub(r" ", text), html
    return text, html


def reformat(
    text: str,
    single_hyphens: bool=True,
    page_break: Optional[str]=None,
) -> str:
    if not page_break:
        return reformat_page(text, single_hyphens=single_hyphens)
    else:
        return f"\n{page_break}\n".join(
            reformat_page(text_page.strip(), single_hyphens=single_hyphens)
            for text_page in text.split(page_break)
        )


def reformat_page(text: str, single_hyphens: bool=True) -> str:
    text = SPACES_RE.sub(r" ", text)
    if single_hyphens:
        text = HYPHENS_RE.sub(r"\1\2", text)
    else:
        pass
        text = HYPHENSHASH_RE.sub(r"\1\2", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = LINEBREAKS_RE.sub("\n\n", text)
    blocks = []
    for block in text.split("\n\n"):
        lines = []
        for line in block.split("\n"):
            if all(char in string.digits for char in line if char != ""):
                lines.append("\n" + line.strip() + "\n")
            else:
                lines.append(line.strip())
        blocks.append(" ".join(lines).strip())
    text = "\n\n".join(blocks)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def get_text_pdfminer(
    filename: str,
    line_margin: float=0.15,
    detect_vertical: bool=-0.8,
    all_texts: bool=False,
    boxes_flow: Optional[float]=None,
    same_sizes: Optional[bool]=False,
    occurrence_rate: Optional[bool]=None,
    page_break: Optional[str]=None,
    contents: Optional[io.BytesIO]=None,
) -> str:
    text = ""
    html = None
    laparams = LAParams(
        line_margin=line_margin,
        boxes_flow=boxes_flow,
        detect_vertical=detect_vertical,
        all_texts=False
    )
    pages = list(extract_pages(filename, laparams=laparams))
    font, size, _ = get_most_frequent_and_largest_fonts(pages)
    text = get_text(pages, font, size, page_break)
    if len(text.strip()) == 0 and all_texts:
        text, html = get_all_texts(
            filename,
            line_margin=line_margin,
            boxes_flow=boxes_flow,
            detect_vertical=detect_vertical,
        )
    return reformat(text, page_break=page_break).strip(), html


def get_text_fitz(
    filename: str,
    line_margin: float=0.15,
    detect_vertical: bool=-0.8,
    all_texts: bool=False,
    boxes_flow: Optional[float]=None,
    same_sizes: Optional[bool]=False,
    occurrence_rate: Optional[bool]=None,
    page_break: Optional[str]=None,
    contents: Optional[io.BytesIO]=None,
) -> str:
    faulthandler.enable()
    # Disable ascender/descender values as per
    # https://github.com/pymupdf/PyMuPDF/issues/930 and
    # https://bugs.ghostscript.com/show_bug.cgi?id=703649
    fitz.TOOLS.mupdf_display_errors(False)
    fitz.TOOLS.mupdf_display_warnings(False)
    fitz.TOOLS.unset_quad_corrections(True)
    if contents is None:
        pdf = fitz.open(filename)
    else:
        pdf = fitz.Document(stream=contents, filetype=filename.name)
    text = []
    for page in pdf:
        fonts = []
        lengths = []
        page_dict = page.get_text("dict", flags=0)
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                line_text = ""
                chars = ""
                for span in line.get("spans", []):
                    span_font = span.get("font", "").split(",")[0].split("-")[0]
                    span_text = span.get("text", "")
                    chars = ""
                    for char in span_text:
                        if char.strip() != "":
                            fonts.append((span_font, span["size"], span["color"]))
                            chars += char
                    line_text += span_text.strip()
                if chars:
                    lengths.append(len(chars))
        if not fonts or not lengths:
            continue
        if occurrence_rate is not None:
            counts = Counter(fonts)
            freqs = [(i, counts[i] / len(fonts))
                     for i, count in counts.most_common()]
            font_tuples = set(
                font_tuple for font_tuple, freq in freqs
                if freq >= occurrence_rate
            )
            font, size, color = list(zip(*font_tuples))
        else:
            font, size, color = Counter(fonts).most_common(1)[0][0]
            font, size, color = [font], [size], [color]
        font, size, color = set(font), set(size), set(color)
        # if len(lengths) > 1:
        #     lengths_std = statistics.stdev(lengths)
        #     lengths_mean = statistics.mean(lengths)
        # else:
        #     lengths_std = 0  # Not sure about this
        #     lengths_mean = len(lengths)
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                line_text = ""
                for span_index, span in enumerate(line.get("spans", [])):
                    span_text = span["text"].strip()
                    if (span_text
                        and any(span["font"].startswith(f) for f in font)
                        and any(span["color"] == c for c in color)
                        and (any(span["size"] == s for s in size)
                             or not same_sizes)
                        and span["flags"] in (0, 4, 6)
                        and line["wmode"] == 0
                        ):
                        line_text += span["text"]
                    if len(line_text) > 2 and line_text.rstrip()[-1] == "-":
                        line_text += "#"
                text.append(line_text)
                text.append(" ")
            text.append("\n")
        text.append("\n")
        if page_break and "".join(text).strip():
            text.append(page_break)
    text = reformat("".join(text), page_break=page_break, single_hyphens=False)
    if "-#" in text:
        text = text.replace("-#", "-")
    return text, None


def get_text_from_pdf_or_tar(
    filename: str,
    pdfs_dir: Union[Path, str],
    output: Union[Path, str],
    overwrite: bool=False,
    bar: Optional[tqdm]=None,
    line_margin: float=0.15,
    detect_vertical: bool=-0.8,
    all_texts: bool=False,
    boxes_flow: Optional[float]=None,
    skip_empty: Optional[bool]=True,
    same_sizes: Optional[bool]=False,
    occurrence_rate: Optional[bool]=None,
    page_break: Optional[str]=None,
) -> NoReturn:
    if ".tar" in filename.suffixes or ".tgz" in filename.suffixes:
        if ".gz" in filename.suffixes or ".tgz" in filename.suffixes:
            mode = "r:gz'"
        else:
            mode = "r"
        tar = tarfile.open(filename, mode=mode)
        if bar is not None:
            pdf_names = tqdm(tar.getnames(), desc="  - ")
        else:
            pdf_names = tar.getnames()
        for pdf_name in pdf_names:
            if pdf_name.endswith(".pdf"):
                pdf_file = tar.extractfile(pdf_name)
                pdf_bytes = io.BytesIO(pdf_file.read())
                get_text_from_pdf(
                    filename=Path(pdf_name),
                    pdfs_dir=pdfs_dir,
                    output=output,
                    overwrite=overwrite,
                    bar=bar,
                    line_margin=line_margin,
                    detect_vertical=detect_vertical,
                    all_texts=all_texts,
                    boxes_flow=boxes_flow,
                    skip_empty=skip_empty,
                    same_sizes=same_sizes,
                    occurrence_rate=occurrence_rate,
                    page_break=page_break,
                    contents=pdf_bytes,
                )
    else:
        get_text_from_pdf(
            filename=filename,
            pdfs_dir=pdfs_dir,
            output=output,
            overwrite=overwrite,
            bar=bar,
            line_margin=line_margin,
            detect_vertical=detect_vertical,
            all_texts=all_texts,
            boxes_flow=boxes_flow,
            skip_empty=skip_empty,
            same_sizes=same_sizes,
            occurrence_rate=occurrence_rate,
            page_break=page_break,
        )


def get_text_from_pdf(
    filename: str,
    pdfs_dir: Union[Path, str],
    output: Union[Path, str],
    overwrite: bool=False,
    bar: Optional[tqdm]=None,
    line_margin: float=0.15,
    detect_vertical: bool=-0.8,
    all_texts: bool=False,
    boxes_flow: Optional[float]=None,
    skip_empty: Optional[bool]=True,
    same_sizes: Optional[bool]=False,
    occurrence_rate: Optional[bool]=None,
    page_break: Optional[str]=None,
    contents: Optional[io.BytesIO]=None,
) -> NoReturn:
    """Writes PDFs to text files"""
    logger = get_logger()
    if bar:
        bar.set_description(filename.name)
    if not pdfs_dir.endswith("/"):
        pdfs_dir = f"{pdfs_dir}/"
    dest = Path(output)
    dest_stem = str(filename).replace(str(pdfs_dir), "").rsplit(".pdf", 1)[0]
    text_dest = dest / f"{dest_stem}.txt"
    if not overwrite and text_dest.exists():
        return
    # Create the empty file if it doesn't exist
    text_dest.parent.mkdir(parents=True, exist_ok=True)
    with text_dest.open(mode="a") as _: pass
    if contents is None:
        description = f"{filename} ({sizeof_fmt(filename.stat().st_size)})"
    else:
        description = f"{filename} ({sizeof_fmt(len(contents.getvalue()))})"
    get_text = get_text_pdfminer if args.engine == "pdf2txt" else get_text_fitz
    text = ""
    html = None
    try:
        with time_limit(args.timeout, description=description):
            text, html = get_text(
                filename, line_margin, detect_vertical, all_texts, boxes_flow,
                same_sizes, occurrence_rate, page_break, contents
            )
        if not text and skip_empty:
            dest = dest / "empty"
    except TimeoutException as exception:
        dest = dest / "timeout"
        text = traceback.format_exc()
        logger.error(description)
        logger.error(str(text))
    except Exception as exception:
        dest = dest / str(exception.__class__.__name__).lower()
        text = traceback.format_exc()
        logger.error(description)
        logger.error(str(text))
    # heading = get_text(pages, "size", size).strip()
    # heading = reformat(heading)
    # dest.mkdir(parents=True, exist_ok=True)
    text_dest.unlink(missing_ok=True)  # remove temporary file
    text_dest = dest / Path(f"{dest_stem}.txt")
    text_dest.parent.mkdir(parents=True, exist_ok=True)
    with text_dest.open(mode="w") as text_file:
        if args.split_sentences:
            for sentence in SPLITTER.split(text=text):
                text_file.write(
                    f"{sentence}\n".encode('utf-8', 'replace').decode()
                )
        else:
            text_file.write(text.encode('utf-8', 'replace').decode())
    # if html is not None:
    #     html_dest = dest / f"{dest_stem}.html"
    #     html_dest.parent.mkdir(parents=True, exist_ok=True)
    #     if not overwrite and html_dest.exists():
    #         return
    #     with html_dest.open(mode="w") as html_file:
    #         html_file.write(html.encode('utf-8', 'replace').decode())


def generate_paths(paths: List, progress_file: str) -> Path:
    with Path(progress_file).open(mode="w") as file:
        for path in paths:
            file.write(str(path) + "\n")
            yield path
    # for path in paths:
    #     if not str(path) in IGNORES:
    #         IGNORES.add(str(path))
    #         with RESUME_FILE.open(mode="a") as resume_file:
    #             resume_file.write(str(path) + "\n")
    #         if resume:
    #             yield path
    #     if not resume:
    #         yield path


def get_page_break(page_break: str) -> str:
    if page_break == "\\f":
        return "\f"
    elif page_break == "\\r":
        return "\r"
    elif page_break == "\\n":
        return "\n"
    elif page_break == "\\t":
        return "\t"
    else:
        return page_break


def main(args: argparse.ArgumentParser) -> NoReturn:
    """Main function"""
    logger = get_logger()
    logger.info("Starting...")
    logger.info(f"Started at {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Reading pdfs: {args.pdfs_dir}/{args.pdfs_glob}")
    logger.info(f"Writing texts: {args.output_dir}")
    logger.info(f"Texts will{' NOT' if args.no_overwrite else ''} be overwritten")
    logger.info(f"All texts will{' NOT' if args.no_all_texts else ''} be extracted")
    logger.info(f"Page breaks are {'not added' if not args.page_break else f'{args.page_break}'}")
    logger.info(f"Progress file: {args.progress_file}")
    logger.info(f"Processing time out of {args.timeout} seconds")
    logger.info(
        f"Running using {'all' if args.n_jobs < 0 else args.n_jobs} processes"
    )
    if not args.total:
        logger.info("Calculating number of files...")
        path = Path(args.pdfs_dir).rglob(args.pdfs_glob)
        total = len(list(None for p in path if p.is_file()))
        logger.info(f"Found {total} pdf files")
    else:
        total = args.total
        logger.info(f"Trusting there are {total} pdf files")
    path = Path(args.pdfs_dir).rglob(args.pdfs_glob)
    bar = tqdm(generate_paths(path, args.progress_file), total=total)
    Parallel(n_jobs=args.n_jobs)(
        delayed(get_text_from_pdf_or_tar)(
            pdf,
            pdfs_dir=args.pdfs_dir,
            output=args.output_dir,
            overwrite=not args.no_overwrite,
            bar=bar if args.n_jobs == 1 else None,
            line_margin=args.line_margin,
            boxes_flow=args.boxes_flow,
            detect_vertical=False,
            all_texts=not args.no_all_texts,
            skip_empty=args.skip_empty,
            same_sizes=args.same_sizes,
            occurrence_rate=args.occurrence_rate or None,
            page_break=get_page_break(args.page_break) if args.page_break else None,
        )
        for step, pdf in enumerate(bar))
    # bar.set_description("Done")
    logger.info(f"Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Done!")


if __name__ == '__main__':
    yesno = lambda x: str(x).lower() in {'true', 't', '1', 'yes', 'y'}
    parser = argparse.ArgumentParser(description=f""
    f"Extracts the text of the body of PDF's with column layout with "
    f"extractable text objects"
    f"", epilog=f"""Example usage:
    {__file__} ./pdfs "*.pdf" ./outputs --timeout 60 --n_jobs 8
    """, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('pdfs_dir',
        help='Directory with the pdfs files'
    )
    parser.add_argument('pdfs_glob', default="*.pdf",
        help='Glob for the directory with the pdf or tar.gz pdf files'
    )
    parser.add_argument('output_dir',
        help='Directory to store output files'
    )
    parser.add_argument('--no_overwrite',
        action="store_true",
        help='Do not overwrite outputs'
    )
    parser.add_argument('--split_sentences',
        action="store_true",
        help='Split sentences'
    )
    parser.add_argument('--n_jobs',
        default=1, type=int,
        help='Number of multiprocessing jobs. Defaults to 1 (-1 for max)',
    )
    parser.add_argument('--timeout',
        default=30, type=int,
        help='Parsing timeout in seconds. Defaults to 30',
    )
    parser.add_argument('--line_margin',
        default=0.25, type=float,
        help='Line margin for PDFMiner.six LTParams. Defaults to 0.25',
    )
    parser.add_argument('--boxes_flow',
        default=-0.8, type=float,
        help='Boxes flow for PDFMiner.six LTParams. Defaults to -0.8',
    )
    parser.add_argument('--same_sizes',
        action="store_true",
        help='Filter out text when its size is not the same size as that of '
             'the most frequent font'
    )
    parser.add_argument('--occurrence_rate',
        default=0.0, type=float,
        help='Filter out text when the frequency of its font family and size '
             'pair is not at least OCCURRENCE_RATE percent [0.0 - 1.0] of the '
             'characters in a page. If not passed, only the most frequent pair '
             'of font family and size will be used'
    )
    parser.add_argument('--page_break',
        default="", type=str,
        help='Add a PAGE_BREAK character between pages.'
    )
    parser.add_argument('--skip_empty',
        action="store_true",
        help='Ignore files if the extraction produced an empty text'
    )
    parser.add_argument('--no_all_texts',
        action="store_true",
        help='Do not extract from texts in or captioning images'
    )
    parser.add_argument('--engine',
        default="mupdf",
        help='Options are "pdf2txt" for PDFMiner or "mupdf" for MuPDF'
    )
    parser.add_argument('--progress_file',
        default=f'avisleser.{NOW.strftime("%Y%m%dT%H%M%S")}.log',
        help='Save the progress to a local file'
    )
    parser.add_argument('--total',
        default=0, type=int,
        help='Total number of files to process. Calculated if not passed',
    )
    args = parser.parse_args()
    main(args)
