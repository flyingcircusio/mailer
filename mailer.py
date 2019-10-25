import cherrypy
import configparser
import email.message
import email.policy
import jinja2
import smtplib
import json


class MailerConfig(object):

    destination = None
    smtp_host = None
    smtp_user = None
    smtp_password = None

    subject = None

    path = '/'              # Cherrypy route to expose the submission on
    redirect = None         # Redirect, otherwise just return {'status': 'OK'}

    template = jinja2.Template(
    """\
Kontaktformular

{% for k, v in data.items() -%}
{{k}}: {{v}}
{% endfor -%}

"""
)

    @staticmethod
    def from_config(file='mailer.cfg'):
        c = MailerConfig()

        p = configparser.RawConfigParser()
        p.read(file)
        main = p['main']

        c.destination = main['destination']
        c.smtp_host = main['smtp_host']
        c.smtp_user = main['smtp_user']
        c.smtp_pass = main['smtp_password']
        c.subject = main.get('subject', 'Form submission')
        c.path = main.get('path', '')
        c.redirect = main.get('redirect')

        if 'template' in main:
            c.template = jinja2.Template(main['template'])

        return c


class StringGenerator(object):

    def __init__(self, config):
        self.config = config

    def _mail(self, subject=None, **data):
        if subject is None:
            subject = self.config.subject
        msg = email.message.EmailMessage(policy=email.policy.SMTP)
        msg["To"] = self.config.destination
        msg["From"] = self.config.destination
        msg["Subject"] = subject
        msg.set_content(config.template.render(**data, data=data))
        with smtplib.SMTP(self.config.smtp_host, timeout=5) as smtp:
            smtp.starttls()
            if self.config.smtp_user:
                smtp.login(self.config.smtp_user, self.config.smtp_pass)
            smtp.sendmail(self.config.destination, self.config.destination, str(msg))
        cherrypy.log(f'Sending mail "{subject}"')
        return str(msg)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def mail(self, **kw):
        self._mail(**kw)
        if self.config.redirect:
            raise cherrypy.HTTPRedirect(self.config.redirect)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(dict(status='ok')).encode('utf-8')


if __name__ == "__main__":
    config = MailerConfig.from_config()
    cherrypy.config.update({"server.socket_port": 9080})
    cherrypy.quickstart(StringGenerator(config), config.path)
