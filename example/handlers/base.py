import webapp2
from webapp2_extras import jinja2
from helpers import is_debug

DEPENDENCY_MANAGER = 'extensions.jinja2_dependency_manager.DependancyManager'

def jinja2_factory(app):
    debug = is_debug()
    config = jinja2.default_config
    config['globals'] = {'debug': debug}
    config['environment_args']['auto_reload'] = not debug
    config['environment_args']['autoescape'] = True
    config['environment_args']['extensions'].append(DEPENDENCY_MANAGER)
    return jinja2.Jinja2(app, config)


class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app, factory=jinja2_factory)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rendered = self.jinja2.render_template(_template, **context)
        dependency_manager = self.jinja2.environment.extensions[DEPENDENCY_MANAGER]
        post_processed = dependency_manager.add_required_content(rendered)
        self.response.write(post_processed)
