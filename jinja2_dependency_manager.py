# This extension adds support for a new {% require %} tag, primarily to
# facilitate packaging frontend code into modules. The require tag allows you to
# specify a dependency for the current page; eiher a CSS file, a JavaScript
# file, or an HTML file. The file will be included at the correct part of the
# final output (as specified in the base template via the placeholder tags
# {% required_css %}, {% required_js %} and {% required_html %}). CSS would
# typically go in the <head> in a <style> tag, while JavaScript and HTML would
# go at the end of the <body>. The type of a referenced file is inferred via its
# file extension, so the extension must be one of "html", "css", or "js".
#
# The content of required files will be included in the final output in an order
# consistent with the dependency graph, so if A requires B then B will come
# before A in the final output. Each file will only appear once in the final
# output no matter how many times it was required.
#
# N.B.: HTML (like CSS and JS) will not be included at the point in the document
# where it was specified via the require tag, so it is only suited for things
# like frontend template code or hidden elements whose place in the DOM
# doesn't really matter.
#
# Circular dependencies are not supported and will cause errors.

from collections import OrderedDict
import logging
import re
import string

from jinja2 import nodes
from jinja2.ext import Extension

TYPES = ["css", "js", "html"]
TEMPLATE_PREFIX = "required_"
OUTPUT_TAGS = ["%s%s" % (TEMPLATE_PREFIX, key) for key in TYPES]
TEMPLATE_TYPES = {key: "%s%s" % (TEMPLATE_PREFIX, key) for key in TYPES}
COMMENT_FORMAT_STRIGS = {
  "html": "<!-- dm_required: {path} (required from {parent_path}) -->",
  "css": "/* dm_required: {path} (required from {parent_path}) */",
  "js": "/* dm_required: {path} (required from {parent_path}) */",
}
CONTENT = "content"
REQUIRED_FROM_FILE = "required_from_filename"


class InvalidRequirePath(Exception):
  pass

class UnrecognizedTag(Exception):
  pass

class InvalidPlaceholders(Exception):
  pass


class DependencyManager(Extension):
  tags = set(["require"] + OUTPUT_TAGS)

  def __init__(self, environment):
    super(DependencyManager, self).__init__(environment)
    environment.extend(dm_context = {})

  def parse(self, parser):
    token = next(parser.stream)
    token_type = token.value
    if token_type.find(TEMPLATE_PREFIX) == 0:
      # This is a placeholder tag, so output the string that we will later
      # replace with the required content. e.g. {% required_css %} is replaced
      # with ${required_css} which will later be replaced with all of the actual
      # css that was specified via require tags (that substitution happens in
      # add_required_content()).
      return nodes.Const("${%s}" % token_type)
    elif token_type == "require":
      file_path_node = parser.parse_expression()
      file_path = file_path_node.value
      if not file_path:
        raise InvalidRequirePath("No path specified.")
      match = re.match(".*\.([^.]+)$", file_path)
      if not match:
        raise InvalidRequirePath("Missing extension in file path '%s'" % file_path)
      file_type = match.group(1)
      if file_type not in TYPES:
        raise InvalidRequirePath("Unrecognized extension '%s' in path '%s'" % (file_type, file_path))

      if file_type in self.environment.dm_context and file_path in self.environment.dm_context[file_type]:
        # We've already encountered a previous {% require %} tag referencing this file, so no need to do anything.
        return nodes.Const("")
      else:
        args = [
          file_path_node,
          nodes.Const(file_type),
          nodes.Const(parser.filename),
        ]
        include_node = nodes.Include(
          file_path_node,
          True, # with context
          False # ignore missing
        )
        return nodes.CallBlock(self.call_method("_aggregate_required_content", args),
                               [], [], [include_node]).set_lineno(token.lineno)
    else:
      raise UnrecognizedTag("Unrecognized tag '%s'" % token_type)


  def _aggregate_required_content(self, file_path, content_type, required_from_filename, caller=None):
    """Save the content of the block in the environment"s dm_context such that
    we can add it to the page in post-processing. The dm_context is grouped by
    type of content, and each piece of content has a file_path that ensures it
    is only included in the final output once."""
    if content_type not in self.environment.dm_context:
      self.environment.dm_context[content_type] = OrderedDict()
    self.environment.dm_context[content_type][file_path] = {
      CONTENT: unicode(caller()),
      REQUIRED_FROM_FILE: required_from_filename # Save the name of the file where the {% require %} tag occurred, for debugging purposes.
    }
    return "" # Intentionally don't output anything to the page for now.


  def add_required_content(self, rendered):
    """This method adds the required dependencies to the final page. It is
    intended to be called after the normal jinja2 render phase."""
    mapping = {}
    for content_type in TYPES:
      content_dict = self.environment.dm_context.get(content_type, {})
      if self.environment.globals.get("debug"):
        # In debug mode, add a comment containing the file path before each piece of content.
        content_list = []
        comment_format_string = COMMENT_FORMAT_STRIGS.get(content_type, "")
        for file_path, entry in content_dict.items():
          content_list.append(comment_format_string.format(path=file_path, parent_path=entry[REQUIRED_FROM_FILE]))
          content_list.append(entry[CONTENT])
      else:
        content_list = [entry[CONTENT] for entry in content_dict.values()]
      mapping[TEMPLATE_TYPES[content_type]] ="\n".join(content_list)
      placeholder_count = rendered.count("${%s}" % TEMPLATE_TYPES[content_type])
      if content_dict and placeholder_count == 0:
        msg = "%s content found with no corresponding {%% %s %%} tag." % (content_type, TEMPLATE_PREFIX + content_type)
        raise InvalidPlaceholders(msg)
      elif content_dict and placeholder_count > 1:
        msg = "Multiple occurances of {%% %s %%} tag found." % (TEMPLATE_PREFIX + content_type)
        raise InvalidPlaceholders(msg)
    tmpl = string.Template(rendered)
    self.environment.dm_context = {}
    return tmpl.safe_substitute(mapping)
