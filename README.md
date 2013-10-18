Jinja2 DependencyManager
=========================

jinja2_dependency_manager is a simple Jinja2 extension which adds support for a
new `{% require %}` tag which is similar to the builtin Jinja2 `{% include %}` tag,
but works a little differently. It allows frontend code to declare dependencies
to facilitate modularity, maintainability, and reusability.

## Motivation & Use Cases

A primary advantage of using the `{% require %}` tag instead of Jinja2's normal
`{% include %}` tag is that it allows CSS (and JavaScript) to be coupled more
tightly to the HTML that it applies to. Suppose you have a form that you include
on several pages called my_form.html and that there is a corresponding CSS file
called my_form.css that contains styles for that form. With normal include tags,
when you include my_form.html on a page you have to remember to also include or
the corresponding my_form.css file.

With the `{% require %}` tag, you can just add a line to the top of my_form.html
that looks like `{% require 'my_form.css' %}` and then whenever you include
my_form.html the CSS will automatically added as well. Even better, if you
include my_form.html more than once on a page, the CSS will only appear once in
the final output.

This allows frontend code to be structured into independent modules that are
easy to reuse. Modules can depend on other modules by requiring them.

## How it works

The require tag allows you to specify a dependency for the current page; either a
CSS file, a JavaScript file, or an HTML file. The file will be included at the
correct part of the final output (as specified in the base template via the
placeholder tags `{% required_css %}`, `{% required_js %}` and `{% required_html %}`).
CSS would typically go in the `<head>` in a `<style>` tag, while JavaScript and HTML
would go at the end of the `<body>`. The type of a referenced file is inferred via
its file extension, so the extension must be one of "html", "css", or "js"
(though adding support for other file types is straightforward).

The content of required files of the same type will be included in the final
output in an order consistent with the dependency graph, so if A requires B then
B will come before A in the final output. Each file will only appear once in the
final output no matter how many times it was required.

*N.B.: HTML (like CSS and JS) will not be included at the point in the document
where it was specified via the require tag, so it is only suited for things
like frontend template code or hidden elements whose place in the DOM
doesn't really matter.*

## Example

The included example project shows how to use jinja2_dependency_manager with
Google AppEngine, and as an example shows a contact form module that has
associated CSS and JavaScript that gets automatically included.

The extension should work with other environments, but has only been tested in
AppEngine.

## Future work

* Support for linking to files via `<link>` or `<script src="...">` tags instead
  of inserting them directly into the final output.
* Support for filetypes like SCSS or CoffeeScript which would be automatically
  compiled down to CSS or JavaScript as part of the rendering process.
* Figuring out a way to make `add_required_content()` be called automatically.
  Currently it has to be called manually.
* Performance improvements.
* The current implementation is probably not suitable for use with threadsafe: true.
